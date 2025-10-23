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
    print(f"  {GREEN}[4]{RESET} Run SLOW tests only")
    print(f"  {GREEN}[5]{RESET} Run tests with COVERAGE report")
    print(f"  {GREEN}[6]{RESET} Run tests with COVERAGE + HTML report")
    print(f"  {GREEN}[7]{RESET} Run specific test file")
    print(f"  {GREEN}[8]{RESET} Run tests matching keyword")
    print(f"  {GREEN}[9]{RESET} Run last failed tests only")
    print(f"  {YELLOW}[v]{RESET} Run in VERBOSE mode (shows each test)")
    print(f"  {YELLOW}[c]{RESET} Check COVERAGE status")
    print(f"  {YELLOW}[r]{RESET} View last test REPORT")
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

    # Build command
    cmd = ["uv", "run", "pytest"] + args

    # Run pytest and capture output
    try:
        # Run with captured output for report
        result = subprocess.run(
            cmd,
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True,
        )

        # Display output to user (with colors)
        output_combined = result.stdout + result.stderr
        print(output_combined)

        # Save report
        save_test_report(output_combined, description, result.returncode)

        return result.returncode

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


def get_test_files() -> list[Path]:
    """Get list of all test files."""
    test_dir = Path(__file__).parent / "tests"
    if not test_dir.exists():
        return []
    return sorted(test_dir.rglob("test_*.py"))


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
            # Run unit tests only
            args = base_args + ["-m", "unit", "tests/"]
            exit_code = run_pytest(args, "Unit tests only")

        elif choice == "3":
            # Run integration tests only
            args = base_args + ["-m", "integration", "tests/"]
            exit_code = run_pytest(args, "Integration tests only")

        elif choice == "4":
            # Run slow tests only
            args = base_args + ["-m", "slow", "tests/"]
            exit_code = run_pytest(args, "Slow tests only")

        elif choice == "5":
            # Run with coverage
            args = base_args + [
                "--cov=risk_manager",
                "--cov-report=term-missing",
                "tests/",
            ]
            exit_code = run_pytest(args, "All tests with coverage")

        elif choice == "6":
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

        elif choice == "7":
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

        elif choice == "8":
            # Run tests matching keyword
            keyword = input(f"\n{BOLD}Enter test keyword (e.g., 'daily_loss'): {RESET}").strip()
            if keyword:
                args = base_args + ["-k", keyword, "tests/"]
                exit_code = run_pytest(args, f"Tests matching: {keyword}")
            else:
                print(f"{RED}No keyword entered{RESET}")
                input(f"\n{BOLD}Press Enter to continue...{RESET}")
                continue

        elif choice == "9":
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

        elif choice == "r":
            # View latest report
            view_latest_report()
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

        input(f"\n{BOLD}Press Enter to continue...{RESET}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Test runner interrupted. Goodbye!{RESET}\n")
        sys.exit(0)
