//! Discovery module for detecting project technologies.
//!
//! Scans a repository to detect what technologies are used based on
//! file extensions, filenames, and file contents.

use crate::config::PreCommitConfig;
use ignore::WalkBuilder;
use regex::Regex;
use std::collections::HashSet;
use std::fs;
use std::path::Path;

// Technology detection indicators
const PYTHON_INDICATORS: &[&str] = &[
    "setup.py",
    "pyproject.toml",
    "requirements.txt",
    "pipfile",
    "poetry.lock",
    "setup.cfg",
    "tox.ini",
    "pytest.ini",
    ".py",
    "manage.py",
    "__init__.py",
];

const JAVASCRIPT_INDICATORS: &[&str] = &[
    "package.json",
    "yarn.lock",
    "package-lock.json",
    "npm-shrinkwrap.json",
    ".js",
    ".mjs",
    ".cjs",
    "webpack.config.js",
    "vite.config.js",
    "rollup.config.js",
    "babel.config.js",
    ".babelrc",
];

const TYPESCRIPT_INDICATORS: &[&str] = &[
    "tsconfig.json",
    "tsconfig.base.json",
    "tsconfig.build.json",
    ".ts",
    ".tsx",
    ".d.ts",
];

const JSX_INDICATORS: &[&str] = &[
    ".jsx",
    ".tsx",
    "next.config.js",
    "gatsby-config.js",
    "react-scripts",
    ".storybook",
];

const GO_INDICATORS: &[&str] = &["go.mod", "go.sum", "main.go", ".go", "vendor"];

const DOCKER_INDICATORS: &[&str] = &[
    "dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    ".dockerignore",
    "dockerfile.dev",
    "dockerfile.prod",
];

const YAML_INDICATORS: &[&str] = &[".yml", ".yaml", "docker-compose.yml", "docker-compose.yaml"];
const JSON_INDICATORS: &[&str] = &[".json"];
const TOML_INDICATORS: &[&str] = &[".toml", "pyproject.toml"];
const XML_INDICATORS: &[&str] = &[".xml"];

/// Discover all files in the given path, respecting .gitignore.
pub fn discover_files(path: &Path) -> HashSet<String> {
    let mut files = HashSet::new();

    let walker = WalkBuilder::new(path)
        .hidden(false)
        .git_ignore(true)
        .git_global(true)
        .git_exclude(true)
        .build();

    for entry in walker.flatten() {
        if entry.file_type().map(|ft| ft.is_file()).unwrap_or(false) {
            let file_name = entry.file_name().to_string_lossy().to_lowercase();
            files.insert(file_name.clone());

            // Also add file extension
            if let Some(ext) = entry.path().extension() {
                files.insert(format!(".{}", ext.to_string_lossy().to_lowercase()));
            }
        }
    }

    files
}

/// Check if files contain any of the given indicators.
fn has_indicator(files: &HashSet<String>, indicators: &[&str]) -> bool {
    indicators
        .iter()
        .any(|ind| files.contains(&ind.to_lowercase()))
}

/// Detect if this is a Python project.
pub fn detect_python(files: &HashSet<String>) -> bool {
    has_indicator(files, PYTHON_INDICATORS)
}

/// Detect if project uses uv with uv.lock file.
pub fn detect_uv_lock(files: &HashSet<String>) -> bool {
    files.contains("uv.lock")
}

/// Detect if this is a JavaScript project.
pub fn detect_javascript(files: &HashSet<String>) -> bool {
    has_indicator(files, JAVASCRIPT_INDICATORS)
}

/// Detect if project uses TypeScript.
pub fn detect_typescript(files: &HashSet<String>) -> bool {
    has_indicator(files, TYPESCRIPT_INDICATORS)
}

/// Detect if project uses JSX/React.
pub fn detect_jsx(files: &HashSet<String>) -> bool {
    has_indicator(files, JSX_INDICATORS)
}

/// Detect if this is a Go project.
pub fn detect_go(files: &HashSet<String>) -> bool {
    has_indicator(files, GO_INDICATORS)
}

/// Detect if project uses Docker.
pub fn detect_docker(files: &HashSet<String>) -> bool {
    has_indicator(files, DOCKER_INDICATORS)
}

/// Detect if project uses GitHub Actions.
pub fn detect_github_actions(path: &Path) -> bool {
    let workflows_dir = path.join(".github").join("workflows");
    if workflows_dir.is_dir() {
        if let Ok(entries) = fs::read_dir(&workflows_dir) {
            for entry in entries.flatten() {
                let path = entry.path();
                if let Some(ext) = path.extension() {
                    let ext_str = ext.to_string_lossy().to_lowercase();
                    if ext_str == "yml" || ext_str == "yaml" {
                        return true;
                    }
                }
            }
        }
    }
    false
}

/// Detect YAML files.
pub fn detect_yaml(files: &HashSet<String>) -> bool {
    has_indicator(files, YAML_INDICATORS)
}

/// Detect JSON files.
pub fn detect_json(files: &HashSet<String>) -> bool {
    has_indicator(files, JSON_INDICATORS)
}

/// Detect TOML files.
pub fn detect_toml(files: &HashSet<String>) -> bool {
    has_indicator(files, TOML_INDICATORS)
}

/// Detect XML files.
pub fn detect_xml(files: &HashSet<String>) -> bool {
    has_indicator(files, XML_INDICATORS)
}

/// Attempt to detect Python version from project files.
pub fn detect_python_version(path: &Path) -> Option<String> {
    // Check pyproject.toml
    let pyproject_path = path.join("pyproject.toml");
    if pyproject_path.exists() {
        if let Ok(content) = fs::read_to_string(&pyproject_path) {
            if let Ok(parsed) = content.parse::<toml::Table>() {
                if let Some(project) = parsed.get("project").and_then(|p| p.as_table()) {
                    if let Some(requires_python) =
                        project.get("requires-python").and_then(|r| r.as_str())
                    {
                        // Extract first Python version token, e.g. ">=3.11,<4" -> "python3.11"
                        let re = Regex::new(r"(\d+\.\d+(?:\.\d+)?)").unwrap();
                        if let Some(caps) = re.captures(requires_python) {
                            return Some(format!("python{}", &caps[1]));
                        }
                    }
                }
            }
        }
    }

    // Check .python-version file
    let python_version_path = path.join(".python-version");
    if python_version_path.exists() {
        if let Ok(content) = fs::read_to_string(&python_version_path) {
            let version = content.trim();
            if !version.is_empty() {
                if version.starts_with("python") {
                    return Some(version.to_string());
                } else {
                    return Some(format!("python{}", version));
                }
            }
        }
    }

    None
}

/// Discover project configuration by analyzing files.
pub fn discover_config(path: &Path) -> PreCommitConfig {
    let files = discover_files(path);

    let has_python = detect_python(&files);
    let has_js = detect_javascript(&files);
    let has_typescript = detect_typescript(&files);
    let has_jsx = detect_jsx(&files);
    let has_go = detect_go(&files);
    let has_docker = detect_docker(&files);
    let has_github_actions = detect_github_actions(path);

    let has_yaml = detect_yaml(&files);
    let has_json = detect_json(&files);
    let has_toml = detect_toml(&files);
    let has_xml = detect_xml(&files);

    let python_version = if has_python {
        detect_python_version(path)
    } else {
        None
    };

    PreCommitConfig {
        python_version,
        yaml_check: has_yaml,
        json_check: has_json,
        toml_check: has_toml,
        xml_check: has_xml,
        case_conflict: true, // Always enable for cross-platform compatibility
        executables: true,   // Always enable for shell script safety
        symlinks: false,
        python_base: has_python,
        python: has_python,
        uv_lock: detect_uv_lock(&files),
        pyrefly_args: None,
        docker: has_docker,
        dockerfile_linting: true,
        dockerignore_check: false,
        github_actions: has_github_actions,
        workflow_validation: true,
        security_scanning: false,
        js: has_js,
        typescript: has_typescript,
        jsx: has_jsx,
        prettier_config: None,
        eslint_config: None,
        go: has_go,
        go_critic: false,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::HashSet;
    use tempfile::tempdir;

    #[test]
    fn test_detect_python() {
        let mut files = HashSet::new();
        files.insert("pyproject.toml".to_string());
        assert!(detect_python(&files));
    }

    #[test]
    fn test_detect_python_by_extension() {
        let mut files = HashSet::new();
        files.insert(".py".to_string());
        assert!(detect_python(&files));
    }

    #[test]
    fn test_detect_javascript() {
        let mut files = HashSet::new();
        files.insert("package.json".to_string());
        assert!(detect_javascript(&files));
    }

    #[test]
    fn test_detect_go() {
        let mut files = HashSet::new();
        files.insert("go.mod".to_string());
        assert!(detect_go(&files));
    }

    #[test]
    fn test_detect_docker() {
        let mut files = HashSet::new();
        files.insert("dockerfile".to_string());
        assert!(detect_docker(&files));
    }

    #[test]
    fn test_no_false_positives() {
        let files = HashSet::new();
        assert!(!detect_python(&files));
        assert!(!detect_javascript(&files));
        assert!(!detect_go(&files));
        assert!(!detect_docker(&files));
    }

    #[test]
    fn test_detect_python_version_from_pyproject() {
        let tmp = tempdir().unwrap();
        fs::write(
            tmp.path().join("pyproject.toml"),
            "[project]\nrequires-python = \">=3.11,<4\"",
        )
        .unwrap();

        assert_eq!(
            detect_python_version(tmp.path()),
            Some("python3.11".to_string())
        );
    }

    #[test]
    fn test_detect_python_version_patch_version() {
        let tmp = tempdir().unwrap();
        fs::write(
            tmp.path().join("pyproject.toml"),
            "[project]\nrequires-python = \">=3.10.5\"",
        )
        .unwrap();

        assert_eq!(
            detect_python_version(tmp.path()),
            Some("python3.10.5".to_string())
        );
    }

    #[test]
    fn test_detect_python_version_from_python_version_file() {
        let tmp = tempdir().unwrap();
        fs::write(tmp.path().join(".python-version"), "3.12.1\n").unwrap();

        assert_eq!(
            detect_python_version(tmp.path()),
            Some("python3.12.1".to_string())
        );
    }
}
