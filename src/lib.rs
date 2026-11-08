use std::fs;
use std::path::Path;

/// One match: (path, 1-based line number, line text).
pub type Hit = (String, usize, String);

/// Pure-Rust core: search files for a literal pattern. No Python involved.
pub fn search(paths: &[String], pattern: &str) -> Vec<Hit> {
    let mut hits = Vec::new();
    for p in paths {
        let Ok(bytes) = fs::read(Path::new(p)) else { continue };
        let text = String::from_utf8_lossy(&bytes);
        for (i, line) in text.lines().enumerate() {
            if line.contains(pattern) {
                hits.push((p.clone(), i + 1, line.to_string()));
            }
        }
    }
    hits
}

#[cfg(feature = "python")]
mod py {
    use pyo3::prelude::*;

    /// Python-facing wrapper. Releases the GIL while Rust does the work.
    #[pyfunction]
    fn search(py: Python<'_>, paths: Vec<String>, pattern: String) -> Vec<super::Hit> {
        py.detach(|| super::search(&paths, &pattern))
    }

    #[pymodule]
    fn hybrid_search(m: &Bound<'_, PyModule>) -> PyResult<()> {
        m.add_function(wrap_pyfunction!(search, m)?)?;
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn finds_literal() {
        let dir = std::env::temp_dir().join("hs_test.txt");
        fs::write(&dir, "alpha\nfn main() {}\nbeta fn\n").unwrap();
        let hits = search(&[dir.to_string_lossy().into()], "fn");
        assert_eq!(hits.len(), 2);
        assert_eq!(hits[0].1, 2);
        assert_eq!(hits[1].1, 3);
    }
}
