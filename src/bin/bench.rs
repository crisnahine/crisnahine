// Times the pure-Rust search in-process (no Python, no JSON), same corpus as bench.py.
use std::time::Instant;
fn main() {
    let dir = std::env::args().nth(1).expect("corpus dir");
    let runs: usize = std::env::args().nth(2).map(|s| s.parse().unwrap()).unwrap_or(30);
    let mut paths: Vec<String> = std::fs::read_dir(&dir).unwrap()
        .map(|e| e.unwrap().path().to_string_lossy().into_owned()).collect();
    paths.sort();
    let mut t = Vec::with_capacity(runs);
    let mut n = 0;
    hybrid_search::search(&paths, "fn handler_"); // warm-up
    for _ in 0..runs {
        let s = Instant::now();
        n = hybrid_search::search(&paths, "fn handler_").len();
        t.push(s.elapsed().as_secs_f64() * 1000.0);
    }
    t.sort_by(|a, b| a.partial_cmp(b).unwrap());
    println!("{} {:.2} {:.2} {:.2}", n, t[0], t[runs / 2], t[runs - 1]);
}
