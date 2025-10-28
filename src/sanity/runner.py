"""
Sanity Check Runner - Orchestrates All Sanity Checks

Runs multiple sanity checks in sequence with options for:
- Quick mode (fast checks only)
- Full mode (all checks including enforcement)
- Individual checks

Exit Codes:
0 = All checks passed
1 = At least one check failed
2 = Configuration error
"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env file first
load_dotenv()

# Add project root and src to path
project_root = Path(__file__).parent.parent.parent
src_dir = project_root / "src"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_dir))


class SanityRunner:
    """Orchestrates all sanity checks."""

    def __init__(self):
        self.results = {}

    def print_header(self):
        """Print runner header."""
        print("=" * 70)
        print(" " * 17 + "SANITY CHECK SUITE")
        print("=" * 70)
        print()
        print("Running all sanity checks to verify external dependencies...")
        print()

    def print_summary(self):
        """Print summary of all checks."""
        print()
        print("=" * 70)
        print(" " * 23 + "SUMMARY")
        print("=" * 70)
        print()

        for check_name, result in self.results.items():
            status = "PASSED" if result == 0 else "FAILED"
            symbol = "+" if result == 0 else "x"
            print(f"  [{symbol}] {check_name}: {status} (exit code: {result})")

        print()

        # Overall result
        all_passed = all(code == 0 for code in self.results.values())
        if all_passed:
            print("=" * 70)
            print(" " * 18 + "[+] ALL CHECKS PASSED")
            print("=" * 70)
        else:
            print("=" * 70)
            print(" " * 18 + "[x] SOME CHECKS FAILED")
            print("=" * 70)

        print()

    async def run_auth_check(self) -> int:
        """Run auth sanity check."""
        print("-" * 70)
        print("CHECK 1: Authentication Sanity")
        print("-" * 70)
        print()

        from src.sanity.auth_sanity import AuthSanityCheck
        checker = AuthSanityCheck()
        result = await checker.run()
        self.results["Auth"] = result
        return result

    async def run_events_check(self) -> int:
        """Run events sanity check."""
        print()
        print("-" * 70)
        print("CHECK 2: Events Sanity")
        print("-" * 70)
        print()

        from src.sanity.events_sanity import EventsSanityCheck
        checker = EventsSanityCheck()
        result = await checker.run()
        self.results["Events"] = result
        return result

    async def run_logic_check(self) -> int:
        """Run logic sanity check."""
        print()
        print("-" * 70)
        print("CHECK 3: Logic Sanity")
        print("-" * 70)
        print()

        from src.sanity.logic_sanity import LogicSanityCheck
        checker = LogicSanityCheck()
        result = await checker.run()
        self.results["Logic"] = result
        return result

    async def run_enforcement_check(self) -> int:
        """Run enforcement sanity check."""
        print()
        print("-" * 70)
        print("CHECK 4: Enforcement Sanity")
        print("-" * 70)
        print()

        from src.sanity.enforcement_sanity import EnforcementSanityCheck
        checker = EnforcementSanityCheck()
        result = await checker.run()
        self.results["Enforcement"] = result
        return result

    async def run_quick(self) -> int:
        """
        Run quick sanity checks (auth + events).

        Returns:
            0 if all passed, 1 if any failed
        """
        self.print_header()
        print("MODE: QUICK (Auth + Events)")
        print()

        # Run auth check
        auth_result = await self.run_auth_check()

        # Run events check
        events_result = await self.run_events_check()

        # Summary
        self.print_summary()

        # Return 0 only if all passed
        return 0 if all(r == 0 for r in [auth_result, events_result]) else 1

    async def run_full(self) -> int:
        """
        Run full sanity checks (auth + events + logic + enforcement).

        Returns:
            0 if all passed, 1 if any failed
        """
        self.print_header()
        print("MODE: FULL (Auth + Events + Logic + Enforcement)")
        print()

        # Run auth check
        auth_result = await self.run_auth_check()

        # Only continue if auth passed
        if auth_result != 0:
            print()
            print("WARNING: Auth check failed. Skipping remaining checks.")
            self.print_summary()
            return 1

        # Run events check
        events_result = await self.run_events_check()

        # Run logic check
        logic_result = await self.run_logic_check()

        # Run enforcement check (even if others failed, to get full picture)
        enforcement_result = await self.run_enforcement_check()

        # Summary
        self.print_summary()

        # Return 0 only if all passed
        return 0 if all(r == 0 for r in [auth_result, events_result, logic_result, enforcement_result]) else 1

    async def run_single(self, check_name: str) -> int:
        """
        Run a single sanity check.

        Args:
            check_name: Name of check ("auth", "events", "logic", "enforcement")

        Returns:
            Exit code from check
        """
        check_name_lower = check_name.lower()

        if check_name_lower == "auth":
            return await self.run_auth_check()
        elif check_name_lower == "events":
            return await self.run_events_check()
        elif check_name_lower == "logic":
            return await self.run_logic_check()
        elif check_name_lower == "enforcement":
            return await self.run_enforcement_check()
        else:
            print(f"[x] Unknown check: {check_name}")
            print("  Available checks: auth, events, logic, enforcement")
            return 1


async def main():
    """Main entry point."""
    runner = SanityRunner()

    # Parse command line arguments
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()

        if mode == "quick":
            exit_code = await runner.run_quick()
        elif mode == "full":
            exit_code = await runner.run_full()
        elif mode in ["auth", "events", "logic", "enforcement"]:
            exit_code = await runner.run_single(mode)
        elif mode in ["-h", "--help", "help"]:
            print("=" * 70)
            print(" " * 17 + "SANITY CHECK RUNNER")
            print("=" * 70)
            print()
            print("Usage:")
            print("  python src/sanity/runner.py [mode]")
            print()
            print("Modes:")
            print("  quick           - Quick checks (auth + events, ~10s)")
            print("  full            - Full checks (auth + events + logic + enforcement, ~30s)")
            print("  auth            - Auth check only")
            print("  events          - Events check only")
            print("  logic           - Logic check only")
            print("  enforcement     - Enforcement check only")
            print()
            print("Exit Codes:")
            print("  0 = All checks passed")
            print("  1 = At least one check failed")
            print("  2 = Configuration error")
            print()
            print("Examples:")
            print("  python src/sanity/runner.py quick")
            print("  python src/sanity/runner.py full")
            print("  python src/sanity/runner.py events")
            return 0
        else:
            print(f"[x] Unknown mode: {mode}")
            print("  Use 'python src/sanity/runner.py --help' for usage")
            return 1
    else:
        # Default to full mode
        exit_code = await runner.run_full()

    return exit_code


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
