"""Cross-platform verification run by CI on Linux, macOS and Windows.

Checks, on the current OS:
  1. The single abi3 wheel installs and works on three native Python versions
     (3.10, 3.12, 3.13; on Windows ARM64, where official installers start at 3.11: 3.11, 3.12, 3.13).
  2. demo.py: PyO3 module, Rust CLI and pure Python give identical results.
  3. Python threads calling Rust run in parallel (GIL released).
Exits non-zero on any failure.
"""
import glob
import os
import platform
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
wheels = glob.glob(os.path.join(ROOT, "dist", "*abi3*.whl"))
assert len(wheels) == 1, f"expected one abi3 wheel, found {wheels}"
wheel = wheels[0]
print(f"OS: {platform.system()} {platform.machine()} | wheel: {os.path.basename(wheel)}")

CHECK = (
    "import sys, os, tempfile, hybrid_search\n"
    "p = os.path.join(tempfile.mkdtemp(), 'a.rs')\n"
    "open(p, 'w').write('x\\nfn main(){}\\n')\n"
    "r = hybrid_search.search([p], 'fn')\n"
    "assert r == [(p, 2, 'fn main(){}')], r\n"
    "import platform\n"
    "print('  Python', sys.version.split()[0], platform.machine(), 'OK')\n"
)


def run(cmd):
    print("$", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True, cwd=ROOT)


def venv_python(venv):
    sub = "Scripts" if os.name == "nt" else "bin"
    exe = "python.exe" if os.name == "nt" else "python"
    return os.path.join(venv, sub, exe)


machine = platform.machine().lower()
win_arm = os.name == "nt" and machine in ("arm64", "aarch64")
# Official python.org Windows ARM64 installers start at 3.11 (older builds were NuGet-only).
versions = ["3.11", "3.12", "3.13"] if win_arm else ["3.10", "3.12", "3.13"]
UV_OS = {"Windows": "windows", "Darwin": "macos", "Linux": "linux"}[platform.system()]
UV_ARCH = {"amd64": "x86_64", "x86_64": "x86_64", "arm64": "aarch64", "aarch64": "aarch64"}[machine]

last = None
for v in versions:
    venv = os.path.join(ROOT, f".ci-venv-{v}")
    # Request a native interpreter explicitly, so no emulated Python is used.
    run(["uv", "venv", "-q", "--clear", "-p", f"cpython-{v}-{UV_OS}-{UV_ARCH}", venv])
    py = venv_python(venv)
    run(["uv", "pip", "install", "-q", "-p", py, wheel])
    run([py, "-c", CHECK])
    last = py

run([last, "demo.py"])

THREADS = (
    "import os, tempfile, time, threading, hybrid_search\n"
    "d = tempfile.mkdtemp(); paths = []\n"
    "for f in range(100):\n"
    "    p = os.path.join(d, f'{f}.txt'); open(p, 'w').write('noise line here\\n' * 20000 + 'needle\\n'); paths.append(p)\n"
    "hybrid_search.search(paths, 'needle')\n"
    "t = time.perf_counter(); [hybrid_search.search(paths, 'needle') for _ in range(4)]; s = time.perf_counter() - t\n"
    "ts = [threading.Thread(target=hybrid_search.search, args=(paths, 'needle')) for _ in range(4)]\n"
    "t = time.perf_counter(); [x.start() for x in ts]; [x.join() for x in ts]; p = time.perf_counter() - t\n"
    "print(f'  cpus={os.cpu_count()} serial={s*1000:.0f}ms threads={p*1000:.0f}ms speedup={s/p:.2f}x')\n"
    "assert (os.cpu_count() or 1) < 2 or s / p > 1.2, 'no parallel speedup: GIL not released?'\n"
)
run([last, "-c", THREADS])
print("ALL CHECKS PASSED on", platform.system(), platform.machine())
