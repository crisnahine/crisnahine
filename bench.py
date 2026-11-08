"""Measures PyO3 boundary overhead: same search, pure Rust vs called from Python."""
import os, statistics, subprocess, sys, tempfile, time
import hybrid_search

RUNS = 30
d = tempfile.mkdtemp()
for f in range(200):
    with open(os.path.join(d, f"file_{f:03}.rs"), "w") as fh:
        for i in range(5000):
            fh.write(f"fn handler_{i}() {{ let x = {i}; }}\n" if i % 97 == 0 else f"// line {i} of file {f}\n")
paths = sorted(os.path.join(d, x) for x in os.listdir(d))

def timeit(fn):
    fn()  # warm-up
    ts = []
    for _ in range(RUNS):
        s = time.perf_counter(); r = fn(); ts.append((time.perf_counter() - s) * 1000)
    return len(r), sorted(ts)

def pure_python():
    hits = []
    for p in paths:
        with open(p, encoding="utf-8", errors="replace") as fh:
            for n, line in enumerate(fh, 1):
                if "fn handler_" in line:
                    hits.append((p, n, line.rstrip("\n")))
    return hits

out = subprocess.run([sys.argv[1], d, str(RUNS)], capture_output=True, text=True, check=True).stdout.split()
rn, rmin, rmed, rmax = int(out[0]), *map(float, out[1:])
pn, pt = timeit(lambda: hybrid_search.search(paths, "fn handler_"))
yn, yt = timeit(pure_python)
assert rn == pn == yn, (rn, pn, yn)
print(f"Corpus: 200 files, 1,000,000 lines, {rn:,} matches; {RUNS} timed runs each after warm-up; cpus={os.cpu_count()}")
print(f"{'Method':<28}{'min':>9}{'median':>9}{'max':>9}  (ms)")
print(f"{'Pure Rust (in-process)':<28}{rmin:>9.2f}{rmed:>9.2f}{rmax:>9.2f}")
print(f"{'Rust via PyO3 from Python':<28}{pt[0]:>9.2f}{statistics.median(pt):>9.2f}{pt[-1]:>9.2f}")
print(f"{'Pure Python':<28}{yt[0]:>9.2f}{statistics.median(yt):>9.2f}{yt[-1]:>9.2f}")
ov = statistics.median(pt) - rmed
print(f"PyO3 boundary overhead (median): {ov:.2f} ms = {ov/rmed*100:.1f}% of Rust time, {ov/rn*1e6:.0f} ns per returned match")
