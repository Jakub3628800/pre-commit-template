//! Template rendering module using MiniJinja.
//!
//! Renders pre-commit configuration YAML from Jinja2 templates.

use crate::config::PreCommitConfig;
use chrono::Utc;
use minijinja::{context, Environment};

/// Package version
const VERSION: &str = env!("CARGO_PKG_VERSION");

// Embed templates at compile time
const TEMPLATE_BASE: &str = include_str!("../templates/base.j2");
const TEMPLATE_PYTHON: &str = include_str!("../templates/python.j2");
const TEMPLATE_DOCKER: &str = include_str!("../templates/docker.j2");
const TEMPLATE_JS: &str = include_str!("../templates/js.j2");
const TEMPLATE_GO: &str = include_str!("../templates/go.j2");
const TEMPLATE_GITHUB_ACTIONS: &str = include_str!("../templates/github_actions.j2");
const TEMPLATE_META: &str = include_str!("../templates/meta.j2");

/// Create a configured MiniJinja environment with all templates loaded.
fn create_environment() -> Environment<'static> {
    let mut env = Environment::new();
    env.add_template("base.j2", TEMPLATE_BASE).unwrap();
    env.add_template("python.j2", TEMPLATE_PYTHON).unwrap();
    env.add_template("docker.j2", TEMPLATE_DOCKER).unwrap();
    env.add_template("js.j2", TEMPLATE_JS).unwrap();
    env.add_template("go.j2", TEMPLATE_GO).unwrap();
    env.add_template("github_actions.j2", TEMPLATE_GITHUB_ACTIONS)
        .unwrap();
    env.add_template("meta.j2", TEMPLATE_META).unwrap();
    env
}

/// Generate hooks for a specific type.
fn generate_hooks(
    env: &Environment,
    hook_type: &str,
    config: &PreCommitConfig,
) -> Result<String, String> {
    let template_name = match hook_type {
        "base" => "base.j2",
        "python" => "python.j2",
        "docker" => "docker.j2",
        "js" => "js.j2",
        "go" => "go.j2",
        "github_actions" => "github_actions.j2",
        _ => return Err(format!("Unsupported hook type: {}", hook_type)),
    };

    let template = env.get_template(template_name).map_err(|e| e.to_string())?;

    let ctx = match hook_type {
        "base" => context! {
            yaml => config.yaml_check,
            json => config.json_check,
            toml => config.toml_check,
            xml => config.xml_check,
            case_conflict => config.case_conflict,
            executables => config.executables,
            symlinks => config.symlinks,
            python => config.python_base,
        },
        "python" => context! {
            uv_lock => config.uv_lock,
            pyrefly_args => config.pyrefly_args,
        },
        "docker" => context! {
            dockerfile_linting => config.dockerfile_linting,
            dockerignore_check => config.dockerignore_check,
        },
        "js" => context! {
            typescript => config.typescript,
            jsx => config.jsx,
            prettier_config => config.prettier_config,
            eslint_config => config.eslint_config,
        },
        "go" => context! {
            go_critic => config.go_critic,
        },
        "github_actions" => context! {
            workflow_validation => config.workflow_validation,
            security_scanning => config.security_scanning,
        },
        _ => context! {},
    };

    template.render(ctx).map_err(|e| e.to_string())
}

/// Indent each line of text by the specified number of spaces.
fn indent(text: &str, spaces: usize) -> String {
    let prefix = " ".repeat(spaces);
    text.lines()
        .map(|line| {
            if line.is_empty() {
                line.to_string()
            } else {
                format!("{}{}", prefix, line)
            }
        })
        .collect::<Vec<_>>()
        .join("\n")
}

/// Render the complete pre-commit configuration.
pub fn render_config(config: &PreCommitConfig) -> Result<String, String> {
    let env = create_environment();
    let mut hooks_content = Vec::new();

    // Always add base hooks
    let base_content = generate_hooks(&env, "base", config)?;
    hooks_content.push(base_content);

    // Optional hooks
    if config.python {
        hooks_content.push(generate_hooks(&env, "python", config)?);
    }
    if config.docker {
        hooks_content.push(generate_hooks(&env, "docker", config)?);
    }
    if config.github_actions {
        hooks_content.push(generate_hooks(&env, "github_actions", config)?);
    }
    if config.js {
        hooks_content.push(generate_hooks(&env, "js", config)?);
    }
    if config.go {
        hooks_content.push(generate_hooks(&env, "go", config)?);
    }

    let combined_content = hooks_content.join("\n\n");
    let technologies = config.detected_technologies();
    let timestamp = Utc::now().format("%Y-%m-%dT%H:%M:%SZ").to_string();

    // Render the meta wrapper
    let meta_template = env.get_template("meta.j2").map_err(|e| e.to_string())?;
    let indented_content = indent(&combined_content, 2);

    let mut result = meta_template
        .render(context! {
            content => indented_content,
            python_version => config.python_version,
            version => VERSION,
            timestamp => timestamp,
            technologies => technologies,
        })
        .map_err(|e| e.to_string())?;

    // Ensure trailing newline
    if !result.ends_with('\n') {
        result.push('\n');
    }

    Ok(result)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_render_minimal_config() {
        let config = PreCommitConfig::default();
        let result = render_config(&config);
        assert!(result.is_ok());
        let yaml = result.unwrap();
        assert!(yaml.contains("repos:"));
        assert!(yaml.contains("pre-commit-hooks"));
    }

    #[test]
    fn test_render_python_config() {
        let config = PreCommitConfig {
            python: true,
            python_base: true,
            yaml_check: true,
            ..Default::default()
        };
        let result = render_config(&config);
        assert!(result.is_ok());
        let yaml = result.unwrap();
        assert!(yaml.contains("ruff"));
        assert!(yaml.contains("check-yaml"));
    }

    #[test]
    fn test_render_with_python_version() {
        let config = PreCommitConfig {
            python_version: Some("python3.11".to_string()),
            python: true,
            ..Default::default()
        };
        let result = render_config(&config);
        assert!(result.is_ok());
        let yaml = result.unwrap();
        assert!(yaml.contains("default_language_version:"));
        assert!(yaml.contains("python: python3.11"));
    }

    #[test]
    fn test_indent() {
        let text = "line1\nline2\nline3";
        let indented = indent(text, 2);
        assert_eq!(indented, "  line1\n  line2\n  line3");
    }

    #[test]
    fn test_indent_empty_lines() {
        let text = "line1\n\nline3";
        let indented = indent(text, 2);
        assert_eq!(indented, "  line1\n\n  line3");
    }
}
