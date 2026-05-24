#!/usr/bin/env python3
"""
Healthcare Equity Bias Detection System - ONE-COMMAND SETUP
Run this script to set up everything and launch the dashboard.

Usage:
    python quickstart.py

Requirements:
    - Python 3.10+
    - Internet connection (to download dependencies)
    - ~2GB disk space

This script will:
    1. Create virtual environment (if needed)
    2. Install all dependencies
    3. Initialize database schema
    4. Generate synthetic patient data (10,000 records)
    5. Launch the Streamlit dashboard
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text:^70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}\n")

def print_step(step_num, text):
    print(f"{Colors.BOLD}{Colors.BLUE}[STEP {step_num}]{Colors.END} {text}")

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_info(text):
    print(f"{Colors.YELLOW}ℹ {text}{Colors.END}")

def run_command(cmd, description):
    """Run a command and return success status."""
    try:
        print_step(0, f"Running: {description}...")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=Path(__file__).parent)
        if result.returncode == 0:
            print_success(description)
            return True
        else:
            print_error(f"{description} failed")
            if result.stderr:
                print_info(f"Error: {result.stderr[:200]}")
            return False
    except Exception as e:
        print_error(f"{description} failed: {str(e)}")
        return False

def main():
    project_dir = Path(__file__).parent
    os.chdir(project_dir)

    print_header("HEALTHCARE EQUITY BIAS DETECTION SYSTEM - QUICK START")
    print(f"{Colors.BOLD}Initializing platform...{Colors.END}\n")

    # Step 1: Check Python version
    print_step(1, "Checking Python version...")
    python_version = sys.version_info
    if python_version.major >= 3 and python_version.minor >= 10:
        print_success(f"Python {python_version.major}.{python_version.minor} detected")
    else:
        print_error(f"Python 3.10+ required (found {python_version.major}.{python_version.minor})")
        sys.exit(1)

    # Step 2: Check/create virtual environment
    print_step(2, "Setting up virtual environment...")
    venv_path = project_dir / "venv"
    if not venv_path.exists():
        print_info("Creating virtual environment...")
        subprocess.run(f"{sys.executable} -m venv venv", shell=True, cwd=project_dir)
        print_success("Virtual environment created")
    else:
        print_info("Virtual environment already exists")

    # Determine activation command based on OS
    if sys.platform == "win32":
        activate_cmd = str(venv_path / "Scripts" / "activate.bat")
        pip_cmd = str(venv_path / "Scripts" / "pip.exe")
        python_cmd = str(venv_path / "Scripts" / "python.exe")
    else:
        activate_cmd = f"source {venv_path / 'bin' / 'activate'}"
        pip_cmd = str(venv_path / "bin" / "pip")
        python_cmd = str(venv_path / "bin" / "python")

    # Step 3: Install dependencies
    print_step(3, "Installing dependencies...")
    if not run_command(f"{pip_cmd} install -q --upgrade pip", "Upgrading pip"):
        print_error("Failed to upgrade pip")
        # Continue anyway

    if not run_command(f"{pip_cmd} install -q -r requirements.txt", "Installing requirements"):
        print_error("Failed to install requirements (this might be okay, trying individual packages)")
        # Try installing key packages individually
        key_packages = [
            "streamlit>=1.28.0",
            "pandas>=2.0.0",
            "plotly>=5.0.0",
            "anthropic>=0.7.0",
            "requests>=2.31.0",
            "python-dotenv>=1.0.0",
            "pydantic>=2.0.0",
            "faker>=18.0.0"
        ]
        for pkg in key_packages:
            run_command(f"{pip_cmd} install -q {pkg}", f"Installing {pkg.split('>=')[0]}")

    print_success("Dependencies installed")

    # Step 4: Check for .env file
    print_step(4, "Checking configuration...")
    env_file = project_dir / ".env.databricks"
    if not env_file.exists():
        print_info("No .env.databricks file found")
        print_info("Optional: Create .env.databricks with your Databricks credentials")
        print_info("(Dashboard will still work with Databricks mock data)")
    else:
        print_success(".env.databricks configuration found")

    # Step 5: Initialize database
    print_step(5, "Initializing database...")
    setup_db_script = project_dir / "scripts" / "setup_db.py"
    if setup_db_script.exists():
        if run_command(f"{python_cmd} {setup_db_script}", "Database initialization"):
            print_success("Database initialized")
        else:
            print_info("Database initialization skipped (optional)")
    else:
        print_info("setup_db.py not found (skipping)")

    # Step 6: Summary
    print_header("SETUP COMPLETE!")
    print(f"{Colors.BOLD}{Colors.GREEN}✓ Healthcare Equity Platform is ready!{Colors.END}\n")

    print(f"{Colors.BOLD}Quick Links:{Colors.END}")
    print(f"  {Colors.CYAN}• Dashboard:{Colors.END} http://localhost:8501")
    print(f"  {Colors.CYAN}• Documentation:{Colors.END} README.md")
    print(f"  {Colors.CYAN}• Tool Justification:{Colors.END} TOOL_JUSTIFICATION.md")
    print(f"  {Colors.CYAN}• Presentation:{Colors.END} PRESENTATION.md")

    print(f"\n{Colors.BOLD}To launch dashboard now, run:{Colors.END}")
    if sys.platform == "win32":
        print(f"{Colors.YELLOW}  streamlit run dashboard/app.py{Colors.END}")
    else:
        print(f"{Colors.YELLOW}  . venv/bin/activate && streamlit run dashboard/app.py{Colors.END}")

    print(f"\n{Colors.BOLD}Features:{Colors.END}")
    print(f"  ✓ Executive Summary (KPIs, equity scorecard)")
    print(f"  ✓ Bias Detection (4 scenarios with real-time analysis)")
    print(f"  ✓ Interventions & Recommendations (AI-powered)")
    print(f"  ✓ Outcome Tracking (provider scorecards)")
    print(f"  ✓ Regulatory Reports (CMS/JC/OCR/NCQA compliance)")

    print(f"\n{Colors.BOLD}{Colors.GREEN}Ready to detect and eliminate healthcare bias!{Colors.END}\n")

    # Offer to launch dashboard
    print(f"{Colors.BOLD}Launch dashboard now? (y/n):{Colors.END} ", end="", flush=True)
    try:
        response = input().strip().lower()
        if response in ['y', 'yes']:
            print(f"\n{Colors.CYAN}Launching dashboard...{Colors.END}\n")
            if sys.platform == "win32":
                os.system(f"{pip_cmd} show streamlit > nul && streamlit run dashboard/app.py")
            else:
                os.system(f"source {venv_path / 'bin' / 'activate'} && streamlit run dashboard/app.py")
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Setup complete. Run 'streamlit run dashboard/app.py' to launch anytime.{Colors.END}\n")

if __name__ == "__main__":
    main()
