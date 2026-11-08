"""Free-threaded (no-GIL) Python 3.14 verification, run by CI on every OS.

Checks:
  1. The abi3 wheel is REFUSED by free-threaded 3.14 (confirms abi3 does not cover it).
  2. A version-specific cp314t wheel builds, installs and works.
  3. Importing the module does NOT re-enable the GIL (module declares gil_used = false).
  4. PyO3 module, Rust CLI and pure Python give identical results (demo.py).
  5. Python threads calling Rust run in parallel.
"""
import glob
import os
import platform
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
machine = platform.machine().lower()
UV_OS = {"Windows": "windows", "Darwin": "macos", "Linux": "linux"}[platform.system()]
UV_ARCH = {"amd64": "x86_64", "x86_64": "x86_64", "arm64": "aarch64", "aarch64": "aarch64"}[machine]
SPEC = f"cpython-3.14+freethreaded-{UV_OS}-{UV_ARCH}"


def run(cmd, check=True, **kw):
    print("$", " ".join(cmd), flush=True)
    return subprocess.run(cmd, check=check, cwd=ROOT, **kw)


venv = os.path.join(ROOT, ".ci-venv-3.14t")
run(["uv", "venv", "-q", "--clear", "-p", SPEC, venv])
py = os.path.join(venv, "Scripts" if os.name == "nt" else "bin", "python.exe" if os.name == "nt" else "python")
info = subprocess.run([py, "-c", "import sys,sysconfig,platform;print(sys.version.split()[0], platform.machine(), 'Py_GIL_DISABLED=%s' % sysconfig.get_config_var('Py_GIL_DISABLED'))"],
                      capture_output=True, text=True, check=True).stdout.strip()
print("Interpreter:", info)
assert "Py_GIL_DISABLED=1" in info, "not a free-threaded interpreter"

# 1. abi3 wheel must be refused.
abi3 = glob.glob(os.path.join(ROOT, "dist", "*abi3*.whl"))
assert len(abi3) == 1, abi3
r = run(["uv", "pip", "install", "-q", "-p", py, abi3[0]], check=False, capture_output=True, text=True)
print((r.stdout + r.stderr).strip())
assert r.returncode != 0, "abi3 wheel was accepted by free-threaded Python - unexpected"
print("CONFIRMED: abi3 wheel refused by free-threaded 3.14")

# 2. Build and install a cp314t wheel.
out = os.path.join(ROOT, "dist-ft")
run(["maturin", "build", "--release", "--out", out, "-i", py])
ft = glob.glob(os.path.join(out, "*cp314t*.whl"))
assert len(ft) == 1, f"expected one cp314t wheel, found {os.listdir(out)}"
print("Built:", os.path.basename(ft[0]))
run(["uv", "pip", "install", "-q", "-p", py, ft[0]])

# 3. GIL must stay disabled after import (fails if the module re-enables it).
run([py, "-W", "error::RuntimeWarning", "-c",
     "import sys, hybrid_search; assert not sys._is_gil_enabled(), 'GIL re-enabled'; print('  GIL enabled after import:', sys._is_gil_enabled())"])

# 4. Identical results.
run([py, "demo.py"])

# 5. Parallel threads.
run([py, "-c",
     'import os, statistics, tempfile, time, threading, hybrid_search\n'
    'd = tempfile.mkdtemp(); paths = []\n'
    'for f in range(100):\n'
    "    p = os.path.join(d, f'{f}.txt'); open(p, 'w').write('noise line here\\n' * 20000 + 'needle\\n'); paths.append(p)\n"
    "hybrid_search.search(paths, 'needle')\n"
    'sp = []\n'
    'for trial in range(5):\n'
    "    t = time.perf_counter(); [hybrid_search.search(paths, 'needle') for _ in range(4)]; s = time.perf_counter() - t\n"
    "    ts = [threading.Thread(target=hybrid_search.search, args=(paths, 'needle')) for _ in range(4)]\n"
    '    t = time.perf_counter(); [x.start() for x in ts]; [x.join() for x in ts]; p = time.perf_counter() - t\n'
    "    sp.append(s / p); print(f'  trial {trial+1}: serial={s*1000:.0f}ms threads={p*1000:.0f}ms speedup={s/p:.2f}x')\n"
    'm = statistics.median(sp)\n'
    "print(f'  cpus={os.cpu_count()} median speedup over 5 trials={m:.2f}x (all: ' + ', '.join(f'{x:.2f}' for x in sp) + ')')\n"
    "assert (os.cpu_count() or 1) < 2 or m > 1.2, 'no parallel speedup'\n"])
print("FREE-THREADED CHECKS PASSED on", platform.system(), platform.machine())
