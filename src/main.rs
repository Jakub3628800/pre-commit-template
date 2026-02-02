//! pre-commit-template: Auto-detect technologies and generate pre-commit configuration files.
//!
//! This is the main entry point for the CLI tool.

mod cli;
mod config;
mod discover;
mod render;
mod ui;

use cli::Cli;
use console::style;
use std::fs;
use std::path::Path;
use std::process::Command;

fn main() {
    if let Err(e) = run() {
        ui::print_error(&format!("Error: {}", e));
        std::process::exit(1);
    }
}

fn run() -> Result<(), String> {
    let args = Cli::parse_args();
    let path = args
        .path
        .canonicalize()
        .map_err(|e| format!("Invalid path: {}", e))?;

    if args.interactive {
        run_interactive(&path)
    } else {
        run_auto(&path)
    }
}

/// Run in interactive mode - display UI, collect preferences, output to stdout.
fn run_interactive(path: &Path) -> Result<(), String> {
    println!();
    println!(
        "{}",
        style("╭────────────────────────────────────────────╮")
            .bold()
            .green()
    );
    println!(
        "{}",
        style("│          Pre-commit Starter                │")
            .bold()
            .green()
    );
    println!(
        "{}",
        style("│                                            │").green()
    );
    println!(
        "{}",
        style("│  Generate pre-commit config for your project  │").green()
    );
    println!(
        "{}",
        style("╰────────────────────────────────────────────╯")
            .bold()
            .green()
    );
    println!();

    println!("Analyzing project at: {}", style(path.display()).cyan());
    println!();

    // Detect technologies with spinner
    let spinner = ui::create_spinner("Detecting technologies...");
    let detected_config = discover::discover_config(path);
    spinner.finish_and_clear();

    // Display detected technologies
    ui::display_detected_technologies(&detected_config);

    // Ask if user wants to customize
    let customize = dialoguer::Confirm::new()
        .with_prompt("Would you like to customize the configuration?")
        .default(true)
        .interact()
        .unwrap_or(true);

    let final_config = if customize {
        ui::ask_user_preferences(detected_config)
    } else {
        detected_config
    };

    println!();

    // Generate configuration with spinner
    let spinner = ui::create_spinner("Generating pre-commit configuration...");
    let yaml = render::render_config(&final_config)?;
    spinner.finish_and_clear();

    // Output to stdout in interactive mode
    println!("{}", yaml);

    Ok(())
}

/// Run in auto-generate mode - detect, generate, save, and run pre-commit.
fn run_auto(path: &Path) -> Result<(), String> {
    // Detect technologies
    let config = discover::discover_config(path);

    // Generate YAML
    let yaml = render::render_config(&config)?;

    // Save configuration
    let config_file = path.join(".pre-commit-config.yaml");
    fs::write(&config_file, &yaml).map_err(|e| format!("Failed to write config: {}", e))?;
    ui::print_success(&format!(
        "Configuration saved to {}",
        style(config_file.display()).green()
    ));

    // Install pre-commit hooks
    match Command::new("pre-commit")
        .args(["install"])
        .current_dir(path)
        .output()
    {
        Ok(output) => {
            if !output.status.success() {
                ui::print_error(&format!(
                    "Failed to install pre-commit hooks: {}",
                    String::from_utf8_lossy(&output.stderr)
                ));
            }
        }
        Err(e) => {
            if e.kind() == std::io::ErrorKind::NotFound {
                ui::print_info("pre-commit not found in PATH. Run 'pre-commit install' manually.");
                return Ok(());
            }
            return Err(format!("Failed to run pre-commit: {}", e));
        }
    }

    // Run pre-commit on all files
    match Command::new("pre-commit")
        .args(["run", "--all-files"])
        .current_dir(path)
        .output()
    {
        Ok(output) => {
            if output.status.success() {
                ui::print_success("Pre-commit setup complete and all hooks passed!");
            } else {
                ui::print_info("Pre-commit setup complete but some hooks failed:");
                println!("{}", String::from_utf8_lossy(&output.stdout));
                if !output.stderr.is_empty() {
                    eprintln!("{}", String::from_utf8_lossy(&output.stderr));
                }
            }
        }
        Err(e) => {
            return Err(format!("Failed to run pre-commit hooks: {}", e));
        }
    }

    Ok(())
}
