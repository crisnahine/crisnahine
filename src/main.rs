// Standalone Rust CLI: prints matches as JSON Lines. No Python needed to run it.
fn esc(s: &str) -> String {
    let mut o = String::with_capacity(s.len());
    for c in s.chars() {
        match c {
            '"' => o.push_str("\\\""),
            '\\' => o.push_str("\\\\"),
            '\n' => o.push_str("\\n"),
            '\t' => o.push_str("\\t"),
            c if (c as u32) < 0x20 => o.push_str(&format!("\\u{:04x}", c as u32)),
            c => o.push(c),
        }
    }
    o
}

fn main() {
    let mut args = std::env::args().skip(1);
    let Some(pattern) = args.next() else {
        eprintln!("usage: hsearch PATTERN FILE...");
        std::process::exit(2);
    };
    let paths: Vec<String> = args.collect();
    let hits = hybrid_search::search(&paths, &pattern);
    for (p, n, l) in &hits {
        println!("{{\"path\":\"{}\",\"line\":{},\"text\":\"{}\"}}", esc(p), n, esc(l));
    }
    std::process::exit(if hits.is_empty() { 1 } else { 0 });
}
