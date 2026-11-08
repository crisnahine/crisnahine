# hybrid-verify

Cross-platform verification of a Rust + Python (PyO3 / maturin) hybrid prototype.
CI runs on 6 platforms (Linux, macOS, Windows; x86_64 and ARM64):

- `ci_verify.py` — abi3 wheel on standard Python 3.10/3.12/3.13 (3.11+ on Windows ARM64)
- `ci_freethreaded.py` — free-threaded (no-GIL) Python 3.14 with a cp314t wheel
- `ci_static.py` — fully static musl binary (Linux)

See `.github/workflows/verify.yml`.
