"""Linux static-binary verification: musl build vs default glibc build.

Usage: python ci_static.py <musl-target-triple>
Checks the musl binary is statically linked, gives byte-identical output to the
glibc binary, and reports timing for both (musl's allocator can be slower).
"""
import os
import statistics
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
target = sys.argv[1]
glibc = os.path.join(ROOT, "target", "release", "hsearch")
musl = os.path.join(ROOT, "target", target, "release", "hsearch")

f = subprocess.run(["file", musl], capture_output=True, text=True, check=True).stdout.strip()
print(f)
assert "statically linked" in f or "static-pie linked" in f, "musl binary is not static"
l = subprocess.run(["ldd", musl], capture_output=True, text=True)
print("ldd:", (l.stdout + l.stderr).strip())
assert "not a dynamic executable" in (l.stdout + l.stderr) or "statically linked" in (l.stdout + l.stderr)

d = tempfile.mkdtemp()
paths = []
for i in range(200):
    p = os.path.join(d, f"file_{i:03}.rs")
    with open(p, "w") as fh:
        for n in range(5000):
            fh.write(f"fn handler_{n}() {{}}\n" if n % 97 == 0 else f"// line {n}\n")
    paths.append(p)


def bench(exe):
    outs, ts = None, []
    for _ in range(11):
        s = time.perf_counter()
        r = subprocess.run([exe, "fn handler_", *paths], capture_output=True, check=True)
        ts.append((time.perf_counter() - s) * 1000)
        outs = r.stdout
    return outs, statistics.median(ts)


og, tg = bench(glibc)
om, tm = bench(musl)
assert og == om, "musl and glibc outputs differ"
print(f"Output identical: {len(og.splitlines()):,} JSON lines, {len(og):,} bytes")
print(f"Median of 11 runs: glibc={tg:.1f} ms  musl={tm:.1f} ms  (musl/glibc = {tm/tg:.2f}x)")
print("STATIC BINARY CHECKS PASSED for", target)
