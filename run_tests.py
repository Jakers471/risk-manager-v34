#!/usr/bin/env python3
"""
Test Runner for Risk Manager V34

Interactive menu for running pytest with various options.
Preserves pytest's native colorful output.
Automatically saves test results to test_reports/ for AI review.
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime

# ANSI color codes for the menu
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"

# Test reports directory
REPORTS_DIR = Path(__file__).parent / "test_reports"


def ensure_reports_dir():
    """Ensure test_reports directory exists."""
    REPORTS_DIR.mkdir(exist_ok=True)


def save_test_report(output: str, description: str, exit_code: int):
    """
    Save test results to report files.

    Saves to:
    - test_reports/latest.txt (always overwritten)
    - test_reports/YYYY-MM-DD_HH-MM-SS.txt (timestamped)

    Args:
        output: Test output (stdout + stderr)
        description: Description of test run
        exit_code: pytest exit code
    """
    ensure_reports_dir()

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    status = "PASSED" if exit_code == 0 else "FAILED"

    # Format report
    report = f"""{'=' * 80}
Risk Manager V34 - Test Report
{'=' * 80}
Test Run: {description}
Timestamp: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Status: {status}
Exit Code: {exit_code}
{'=' * 80}

{output}

{'=' * 80}
End of Report
{'=' * 80}
"""

    # Save to latest.txt (always overwritten)
    latest_path = REPORTS_DIR / "latest.txt"
    latest_path.write_text(report, encoding="utf-8")

    # Save to timestamped file
    timestamped_path = REPORTS_DIR / f"{timestamp}_{status.lower()}.txt"
    timestamped_path.write_text(report, encoding="utf-8")

    print(f"\n{GREEN}📄 Test report saved:{RESET}")
    print(f"   {BOLD}Latest:{RESET} test_reports/latest.txt")
    print(f"   {BOLD}Archive:{RESET} test_reports/{timestamp}_{status.lower()}.txt")


def print_header():
    """Print the test runner header."""
    print(f"\n{CYAN}{'=' * 70}{RESET}")
    print(f"{CYAN}{BOLD}   Risk Manager V34 - Test Runner{RESET}")
    print(f"{CYAN}{'=' * 70}{RESET}\n")


def print_menu():
    """Print the test menu options."""
    print(f"{BOLD}Select tests to run:{RESET}\n")
    print(f"  {GREEN}[1]{RESET} Run ALL tests")
    print(f"  {GREEN}[2]{RESET} Run UNIT tests only")
    print(f"  {GREEN}[3]{RESET} Run INTEGRATION tests only")
    print(f"  {GREEN}[4]{RESET} Run E2E tests only")
    print(f"  {GREEN}[5]{RESET} Run SLOW tests only")
    print(f"  {GREEN}[6]{RESET} Run tests with COVERAGE report")
    print(f"  {GREEN}[7]{RESET} Run tests with COVERAGE + HTML report")
    print(f"  {GREEN}[8]{RESET} Run specific test file")
    print(f"  {GREEN}[9]{RESET} Run tests matching keyword")
    print(f"  {GREEN}[0]{RESET} Run last failed tests only")
    print(f"\n  {BOLD}Runtime Checks:{RESET}")
    print(f"  {CYAN}[s]{RESET} Runtime SMOKE (DRY-RUN, fail-fast, 8s timeout)")
    print(f"  {CYAN}[r]{RESET} Runtime SOAK (30-60s DRY-RUN)")
    print(f"  {CYAN}[t]{RESET} Runtime TRACE (ASYNC_DEBUG=1, deep debug)")
    print(f"  {CYAN}[l]{RESET} View/Tail LOGS")
    print(f"  {CYAN}[e]{RESET} Env/Config SNAPSHOT")
    print(f"  {CYAN}[g]{RESET} GATE: Tests + Smoke combo")
    print(f"\n  {YELLOW}[v]{RESET} Run in VERBOSE mode (shows each test)")
    print(f"  {YELLOW}[c]{RESET} Check COVERAGE status")
    print(f"  {YELLOW}[p]{RESET} View last test REPORT")
    print(f"  {YELLOW}[h]{RESET} Help - Testing with AI")
    print(f"  {RED}[q]{RESET} Quit\n")


def run_pytest(args: list[str], description: str) -> int:
    """
    Run pytest with given arguments and save report.

    Args:
        args: List of pytest arguments
        description: Description of what's being run

    Returns:
        Exit code from pytest
    """
    print(f"\n{CYAN}{'─' * 70}{RESET}")
    print(f"{BOLD}Running: {description}{RESET}")
    print(f"{CYAN}{'─' * 70}{RESET}\n")

    # Build command with forced colors
    # Use venv's pytest directly instead of "uv run" to avoid slow dependency resolution
    venv_python = Path(__file__).parent / ".venv" / "bin" / "python"
    if venv_python.exists():
        cmd = [str(venv_python), "-m", "pytest", "--color=yes"] + args
    else:
        # Fallback to uv run if venv not found
        cmd = ["uv", "run", "pytest", "--color=yes"] + args

    # Run pytest with real-time output
    try:
        # Use Popen for real-time output streaming
        process = subprocess.Popen(
            cmd,
            cwd=Path(__file__).parent,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,  # Line buffered
        )

        # Collect output while displaying in real-time
        output_lines = []
        for line in process.stdout:
            print(line, end='')  # Display immediately
            output_lines.append(line)

        # Wait for process to complete
        process.wait()
        output_combined = ''.join(output_lines)

        # Save report
        save_test_report(output_combined, description, process.returncode)

        return process.returncode

    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Tests interrupted by user{RESET}")
        return 1
    except Exception as e:
        error_msg = f"Error running tests: {e}"
        print(f"\n{RED}{error_msg}{RESET}")
        save_test_report(error_msg, description, 1)
        return 1


def view_latest_report():
    """View the latest test report."""
    latest_path = REPORTS_DIR / "latest.txt"

    if not latest_path.exists():
        print(f"\n{YELLOW}No test reports found. Run tests first!{RESET}")
        return

    print(f"\n{CYAN}{'─' * 70}{RESET}")
    print(f"{BOLD}Latest Test Report{RESET}")
    print(f"{CYAN}{'─' * 70}{RESET}\n")

    report = latest_path.read_text(encoding="utf-8")
    print(report)


def print_quick_ai_guide(exit_code: int):
    """Print quick AI command guide after test run."""
    status = "PASSED" if exit_code == 0 else "FAILED"

    print(f"\n{CYAN}{'─' * 70}{RESET}")
    print(f"{BOLD}📋 Quick AI Commands{RESET}")
    print(f"{CYAN}{'─' * 70}{RESET}\n")

    if exit_code == 0:
        print(f"{GREEN}Tests passed!{RESET} To check coverage or add more tests:\n")
        print(f'  {BOLD}→{RESET} "Read htmlcov/index.html and show what needs testing"')
        print(f'  {BOLD}→{RESET} "Read test_reports/latest.txt and suggest more test cases"')
    else:
        print(f"{YELLOW}Tests failed.{RESET} Tell AI to fix them:\n")
        print(f'  {BOLD}→{RESET} "Read test_reports/latest.txt and fix the failing tests"')
        print(f'  {BOLD}→{RESET} "Read test_reports/latest.txt and explain what went wrong"')

    print(f"\n{CYAN}Other useful commands:{RESET}")
    print(f'  {BOLD}→{RESET} "Show me test_reports/ directory" (browse all test runs)')
    print(f'  {BOLD}→{RESET} "Read .claude/agents/README.md" (see available testing agents)')
    print(f'  {BOLD}→{RESET} "Read docs/testing/WORKING_WITH_AI.md" (full AI workflow guide)')

    print(f"\n{CYAN}{'─' * 70}{RESET}")


def show_ai_help():
    """Display help guide for testing with AI."""
    print(f"\n{CYAN}{'=' * 70}{RESET}")
    print(f"{CYAN}{BOLD}   Testing with AI - Quick Guide{RESET}")
    print(f"{CYAN}{'=' * 70}{RESET}\n")

    help_text = f"""{BOLD}How AI Assistants Use Test Reports:{RESET}

{GREEN}1. Test Reports are Auto-Saved{RESET}
   - Every test run saves to: {BOLD}test_reports/latest.txt{RESET}
   - Timestamped archives in: {BOLD}test_reports/YYYY-MM-DD_HH-MM-SS.txt{RESET}
   - AI can read these files to understand test failures

{GREEN}2. Best Workflow for Working with AI:{RESET}
   {YELLOW}a){RESET} Run tests (any option from this menu)
   {YELLOW}b){RESET} Share report with AI: "Read test_reports/latest.txt"
   {YELLOW}c){RESET} AI analyzes failures and suggests fixes
   {YELLOW}d){RESET} Implement fixes, re-run tests
   {YELLOW}e){RESET} Repeat until all tests pass

{GREEN}3. Useful Commands for AI:{RESET}
   {BOLD}"Read test_reports/latest.txt"{RESET}
      → Shows AI the most recent test results

   {BOLD}"Read test_reports/"{RESET} + tab completion
      → Browse archived test reports by timestamp

   {BOLD}"Run tests matching 'keyword'"{RESET}
      → AI can suggest running specific tests (use option 9)

{GREEN}4. Coverage Reports:{RESET}
   - Run option {BOLD}[6]{RESET} for HTML coverage report
   - AI can read: {BOLD}htmlcov/index.html{RESET}
   - Shows which code lacks test coverage

{GREEN}5. Test Organization:{RESET}
   {BOLD}tests/unit/{RESET}        → Fast unit tests
   {BOLD}tests/integration/{RESET} → Integration tests
   {BOLD}tests/e2e/{RESET}         → End-to-end tests

{GREEN}6. Pro Tips:{RESET}
   • Use {BOLD}[v]{RESET} for verbose mode to see individual test names
   • Use {BOLD}[0]{RESET} to re-run only failed tests (faster iteration)
   • Share full test output with AI for better analysis
   • AI can help write new tests based on coverage gaps

{YELLOW}Example AI Conversation:{RESET}
   You: "Read test_reports/latest.txt and fix the failing tests"
   AI:  *Reads report, identifies issues, suggests fixes*
   You: "Apply those changes"
   AI:  *Updates code*
   You: Run option {BOLD}[0]{RESET} to re-run failed tests

{CYAN}{'─' * 70}{RESET}
{BOLD}The test reports are designed to be AI-readable!{RESET}
{CYAN}{'─' * 70}{RESET}
"""
    print(help_text)


def get_test_files() -> list[Path]:
    """Get list of all test files."""
    test_dir = Path(__file__).parent / "tests"
    if not test_dir.exists():
        return []
    return sorted(test_dir.rglob("test_*.py"))


def run_runtime_check(env_vars: dict[str, str], description: str, timeout_s: int = 30) -> int:
    """
    Run a runtime smoke test with specific environment variables.

    Args:
        env_vars: Environment variables to set
        description: Description of the runtime check
        timeout_s: Timeout in seconds for the check

    Returns:
        Exit code from the runtime check
    """
    import os

    print(f"\n{CYAN}{'─' * 70}{RESET}")
    print(f"{BOLD}Running: {description}{RESET}")
    print(f"{CYAN}{'─' * 70}{RESET}\n")

    # Build environment with provided vars
    env = os.environ.copy()
    env.update(env_vars)

    # Display environment settings
    print(f"{BOLD}Environment:{RESET}")
    for key, value in env_vars.items():
        print(f"  {key}={value}")
    print()

    # Run the smoke test
    cmd = [sys.executable, "-m", "src.runtime.smoke_test"]

    try:
        result = subprocess.run(
            cmd,
            cwd=Path(__file__).parent,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )

        # Display output
        output_combined = result.stdout + result.stderr
        print(output_combined)

        # Save report to runtime-specific file
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        runtime_report_path = REPORTS_DIR / f"runtime_{timestamp}.txt"

        report = f"""{'=' * 80}
Risk Manager V34 - Runtime Check Report
{'=' * 80}
Runtime Check: {description}
Timestamp: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Status: {'PASSED' if result.returncode == 0 else 'FAILED'}
Exit Code: {result.returncode}
Environment:
{chr(10).join(f'  {k}={v}' for k, v in env_vars.items())}
{'=' * 80}

{output_combined}

{'=' * 80}
End of Report
{'=' * 80}
"""
        runtime_report_path.write_text(report, encoding="utf-8")

        print(f"\n{GREEN}📄 Runtime report saved:{RESET}")
        print(f"   {BOLD}Report:{RESET} test_reports/runtime_{timestamp}.txt")

        return result.returncode

    except subprocess.TimeoutExpired:
        error_msg = f"Runtime check timed out after {timeout_s}s"
        print(f"\n{RED}{error_msg}{RESET}")

        # Save timeout report
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        runtime_report_path = REPORTS_DIR / f"runtime_{timestamp}_timeout.txt"
        runtime_report_path.write_text(f"Runtime check timed out after {timeout_s}s\n{description}", encoding="utf-8")

        return 1

    except Exception as e:
        error_msg = f"Error running runtime check: {e}"
        print(f"\n{RED}{error_msg}{RESET}")
        return 1


def view_logs():
    """View or tail the risk manager logs."""
    log_path = Path(__file__).parent / "data" / "logs" / "risk_manager.log"

    if not log_path.exists():
        print(f"\n{YELLOW}No log file found at: {log_path}{RESET}")
        print(f"{YELLOW}Run the application first to generate logs.{RESET}")
        return

    print(f"\n{CYAN}{'─' * 70}{RESET}")
    print(f"{BOLD}Log Viewer{RESET}")
    print(f"{CYAN}{'─' * 70}{RESET}\n")

    print(f"{BOLD}Options:{RESET}")
    print(f"  {GREEN}[1]{RESET} View last 50 lines")
    print(f"  {GREEN}[2]{RESET} View last 100 lines")
    print(f"  {GREEN}[3]{RESET} View entire log")
    print(f"  {GREEN}[4]{RESET} Tail log (follow mode)")

    choice = input(f"\n{BOLD}Enter choice: {RESET}").strip()

    if choice == "1":
        result = subprocess.run(["tail", "-n", "50", str(log_path)])
    elif choice == "2":
        result = subprocess.run(["tail", "-n", "100", str(log_path)])
    elif choice == "3":
        result = subprocess.run(["cat", str(log_path)])
    elif choice == "4":
        print(f"\n{CYAN}Following log (Ctrl+C to stop)...{RESET}\n")
        try:
            # Try tail -f first (Linux/Mac), fall back to Python implementation
            subprocess.run(["tail", "-f", str(log_path)])
        except (FileNotFoundError, KeyboardInterrupt):
            pass
    else:
        print(f"\n{RED}Invalid choice{RESET}")


def show_env_snapshot():
    """Display environment and configuration snapshot."""
    import os

    print(f"\n{CYAN}{'=' * 70}{RESET}")
    print(f"{CYAN}{BOLD}   Environment & Configuration Snapshot{RESET}")
    print(f"{CYAN}{'=' * 70}{RESET}\n")

    # Key environment variables
    key_vars = [
        "DRY_RUN",
        "BOOT_TIMEOUT_S",
        "LOG_LEVEL",
        "ASYNC_DEBUG",
        "PYTHONPATH",
        "VIRTUAL_ENV",
    ]

    print(f"{BOLD}Environment Variables:{RESET}")
    for var in key_vars:
        value = os.environ.get(var, f"{YELLOW}(not set){RESET}")
        print(f"  {var}={value}")

    print(f"\n{BOLD}Configuration Paths:{RESET}")
    base_path = Path(__file__).parent

    config_paths = [
        ("Config Directory", base_path / "config"),
        ("Risk Config", base_path / "config" / "risk_config.yaml"),
        ("Accounts Template", base_path / "config" / "accounts.yaml.template"),
        ("Data Directory", base_path / "data"),
        ("Logs Directory", base_path / "data" / "logs"),
        ("Log File", base_path / "data" / "logs" / "risk_manager.log"),
    ]

    for name, path in config_paths:
        status = f"{GREEN}✓{RESET}" if path.exists() else f"{RED}✗{RESET}"
        print(f"  {status} {name}: {path}")

    print(f"\n{BOLD}Python Environment:{RESET}")
    print(f"  Python: {sys.executable}")
    print(f"  Version: {sys.version.split()[0]}")
    print(f"  Platform: {sys.platform}")

    print(f"\n{CYAN}{'─' * 70}{RESET}")


def main():
    """Main test runner loop."""
    verbose_mode = False
    ensure_reports_dir()

    while True:
        print_header()
        print_menu()

        choice = input(f"{BOLD}Enter choice: {RESET}").strip().lower()

        # Build base pytest args
        base_args = []
        if verbose_mode:
            base_args.append("-v")

        # Handle choice
        if choice == "1":
            # Run all tests
            args = base_args + ["tests/"]
            exit_code = run_pytest(args, "All tests")

        elif choice == "2":
            # Run unit tests only (by directory, not marker)
            args = base_args + ["tests/unit/"]
            exit_code = run_pytest(args, "Unit tests only")

        elif choice == "3":
            # Run integration tests only (by directory, not marker)
            args = base_args + ["tests/integration/"]
            exit_code = run_pytest(args, "Integration tests only")

        elif choice == "4":
            # Run E2E tests only
            args = base_args + ["tests/e2e/", "-v"]
            exit_code = run_pytest(args, "E2E tests only")

        elif choice == "5":
            # Run slow tests only
            args = base_args + ["-m", "slow", "tests/"]
            exit_code = run_pytest(args, "Slow tests only")

        elif choice == "6":
            # Run with coverage
            args = base_args + [
                "--cov=risk_manager",
                "--cov-report=term-missing",
                "tests/",
            ]
            exit_code = run_pytest(args, "All tests with coverage")

        elif choice == "7":
            # Run with coverage + HTML
            args = base_args + [
                "--cov=risk_manager",
                "--cov-report=term-missing",
                "--cov-report=html",
                "tests/",
            ]
            exit_code = run_pytest(args, "All tests with coverage + HTML report")
            if exit_code == 0:
                print(
                    f"\n{GREEN}✓ HTML coverage report: {BOLD}htmlcov/index.html{RESET}"
                )

        elif choice == "8":
            # Run specific test file
            print(f"\n{BOLD}Available test files:{RESET}\n")
            test_files = get_test_files()
            if not test_files:
                print(f"{RED}No test files found in tests/{RESET}")
                input(f"\n{BOLD}Press Enter to continue...{RESET}")
                continue

            for idx, test_file in enumerate(test_files, 1):
                rel_path = test_file.relative_to(Path(__file__).parent)
                print(f"  {GREEN}[{idx}]{RESET} {rel_path}")

            file_choice = input(f"\n{BOLD}Enter file number: {RESET}").strip()
            try:
                file_idx = int(file_choice) - 1
                if 0 <= file_idx < len(test_files):
                    test_file = test_files[file_idx]
                    args = base_args + [str(test_file)]
                    exit_code = run_pytest(args, f"Test file: {test_file.name}")
                else:
                    print(f"{RED}Invalid file number{RESET}")
                    input(f"\n{BOLD}Press Enter to continue...{RESET}")
                    continue
            except ValueError:
                print(f"{RED}Invalid input{RESET}")
                input(f"\n{BOLD}Press Enter to continue...{RESET}")
                continue

        elif choice == "9":
            # Run tests matching keyword
            keyword = input(f"\n{BOLD}Enter test keyword (e.g., 'daily_loss'): {RESET}").strip()
            if keyword:
                args = base_args + ["-k", keyword, "tests/"]
                exit_code = run_pytest(args, f"Tests matching: {keyword}")
            else:
                print(f"{RED}No keyword entered{RESET}")
                input(f"\n{BOLD}Press Enter to continue...{RESET}")
                continue

        elif choice == "0":
            # Run last failed tests
            args = base_args + ["--lf", "tests/"]
            exit_code = run_pytest(args, "Last failed tests")

        elif choice == "v":
            # Toggle verbose mode
            verbose_mode = not verbose_mode
            status = "ON" if verbose_mode else "OFF"
            print(f"\n{GREEN}✓ Verbose mode: {BOLD}{status}{RESET}")
            input(f"\n{BOLD}Press Enter to continue...{RESET}")
            continue

        elif choice == "c":
            # Check coverage status
            print(f"\n{CYAN}{'─' * 70}{RESET}")
            print(f"{BOLD}Coverage Status{RESET}")
            print(f"{CYAN}{'─' * 70}{RESET}\n")
            result = subprocess.run(
                ["uv", "run", "coverage", "report"],
                cwd=Path(__file__).parent,
            )
            if result.returncode != 0:
                print(f"\n{YELLOW}No coverage data. Run tests with coverage first (option 5 or 6){RESET}")
            input(f"\n{BOLD}Press Enter to continue...{RESET}")
            continue

        elif choice == "s":
            # Runtime Smoke Test
            env_vars = {
                "DRY_RUN": "1",
                "BOOT_TIMEOUT_S": "8",
                "LOG_LEVEL": "DEBUG",
            }
            exit_code = run_runtime_check(env_vars, "Runtime Smoke Test (DRY-RUN, fail-fast, 8s)", timeout_s=15)

        elif choice == "r":
            # Runtime Soak Test
            env_vars = {
                "DRY_RUN": "1",
                "BOOT_TIMEOUT_S": "60",
            }
            exit_code = run_runtime_check(env_vars, "Runtime Soak Test (30-60s DRY-RUN)", timeout_s=90)

        elif choice == "t":
            # Runtime Trace Test
            env_vars = {
                "ASYNC_DEBUG": "1",
                "DRY_RUN": "1",
            }
            exit_code = run_runtime_check(env_vars, "Runtime Trace (ASYNC_DEBUG, deep debug)", timeout_s=30)

        elif choice == "l":
            # View/Tail Logs
            view_logs()
            input(f"\n{BOLD}Press Enter to continue...{RESET}")
            continue

        elif choice == "e":
            # Environment Snapshot
            show_env_snapshot()
            input(f"\n{BOLD}Press Enter to continue...{RESET}")
            continue

        elif choice == "g":
            # Gate: Unit + Integration + Smoke
            print(f"\n{CYAN}{'=' * 70}{RESET}")
            print(f"{BOLD}Running GATE Check: Unit + Integration + Smoke{RESET}")
            print(f"{CYAN}{'=' * 70}{RESET}\n")

            # Run unit tests
            args = base_args + ["tests/unit/"]
            exit_code_unit = run_pytest(args, "GATE: Unit tests")

            if exit_code_unit != 0:
                print(f"\n{RED}GATE FAILED: Unit tests failed{RESET}")
                exit_code = exit_code_unit
            else:
                # Run integration tests
                args = base_args + ["tests/integration/"]
                exit_code_int = run_pytest(args, "GATE: Integration tests")

                if exit_code_int != 0:
                    print(f"\n{RED}GATE FAILED: Integration tests failed{RESET}")
                    exit_code = exit_code_int
                else:
                    # Run smoke test
                    env_vars = {
                        "DRY_RUN": "1",
                        "BOOT_TIMEOUT_S": "8",
                        "LOG_LEVEL": "DEBUG",
                    }
                    exit_code_smoke = run_runtime_check(env_vars, "GATE: Runtime Smoke", timeout_s=15)

                    if exit_code_smoke != 0:
                        print(f"\n{RED}GATE FAILED: Smoke test failed{RESET}")
                        exit_code = exit_code_smoke
                    else:
                        print(f"\n{GREEN}{'=' * 70}{RESET}")
                        print(f"{GREEN}{BOLD}✓ GATE PASSED: All checks successful!{RESET}")
                        print(f"{GREEN}{'=' * 70}{RESET}")
                        exit_code = 0

        elif choice == "p":
            # View latest report
            view_latest_report()
            input(f"\n{BOLD}Press Enter to continue...{RESET}")
            continue

        elif choice == "h":
            # Show AI help
            show_ai_help()
            input(f"\n{BOLD}Press Enter to continue...{RESET}")
            continue

        elif choice == "q":
            # Quit
            print(f"\n{GREEN}Thanks for testing! 🧪{RESET}\n")
            sys.exit(0)

        else:
            print(f"\n{RED}Invalid choice. Please try again.{RESET}")
            input(f"\n{BOLD}Press Enter to continue...{RESET}")
            continue

        # Show result summary
        if exit_code == 0:
            print(f"\n{GREEN}{'─' * 70}{RESET}")
            print(f"{GREEN}{BOLD}✓ All tests passed!{RESET}")
            print(f"{GREEN}{'─' * 70}{RESET}")
        else:
            print(f"\n{RED}{'─' * 70}{RESET}")
            print(f"{RED}{BOLD}✗ Some tests failed{RESET}")
            print(f"{RED}{'─' * 70}{RESET}")

        # Show quick AI command guide
        print_quick_ai_guide(exit_code)

        input(f"\n{BOLD}Press Enter to continue...{RESET}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Test runner interrupted. Goodbye!{RESET}\n")
        sys.exit(0)
