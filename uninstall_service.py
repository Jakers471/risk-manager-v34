"""
Uninstall Risk Manager V34 Windows Service.

This script uninstalls the Risk Manager Windows Service and optionally
removes configuration and data files.

Requirements:
    - Must be run with Administrator privileges (UAC prompt)
    - Service must be stopped before uninstallation

Usage:
    Right-click terminal → "Run as Administrator"
    python uninstall_service.py [--keep-data]
"""

import argparse
import ctypes
import shutil
import sys
from pathlib import Path

import win32service
import win32serviceutil


def is_admin() -> bool:
    """Check if script is running with admin privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def stop_service() -> None:
    """Stop the service if running."""
    print("\n🛑 Stopping service...")

    try:
        from risk_manager.daemon.service import RiskManagerService

        # Check current status
        status = win32serviceutil.QueryServiceStatus(RiskManagerService._svc_name_)

        if status[1] == win32service.SERVICE_RUNNING:
            # Service is running, stop it
            print("  ⏳ Service is running, stopping...")

            win32serviceutil.StopService(RiskManagerService._svc_name_)

            # Wait for service to stop (up to 30 seconds)
            import time

            for _ in range(30):
                status = win32serviceutil.QueryServiceStatus(RiskManagerService._svc_name_)

                if status[1] == win32service.SERVICE_STOPPED:
                    print("  ✅ Service stopped")
                    return

                time.sleep(1)

            print("  ⚠️  Warning: Service did not stop within 30 seconds")

        elif status[1] == win32service.SERVICE_STOPPED:
            print("  ✅ Service already stopped")

        else:
            print(f"  ℹ️  Service status: {status[1]}")

    except Exception as e:
        print(f"  ⚠️  Warning: Failed to stop service: {e}")


def uninstall_service() -> None:
    """Uninstall Windows Service."""
    print("\n🔧 Uninstalling Windows Service...")

    try:
        from risk_manager.daemon.service import RiskManagerService

        # Remove service
        win32serviceutil.RemoveService(RiskManagerService._svc_name_)

        print(f"  ✅ Service uninstalled: {RiskManagerService._svc_name_}")

    except Exception as e:
        print(f"  ❌ Service uninstallation failed: {e}")
        raise


def remove_data(keep_data: bool = False) -> None:
    """
    Remove data directories.

    Args:
        keep_data: If True, keep configuration and data files
    """
    if keep_data:
        print("\n📁 Keeping configuration and data files...")
        print("  ℹ️  Data location: C:\\ProgramData\\RiskManagerV34")
        return

    print("\n🗑️  Removing data directories...")

    base_dir = Path("C:/ProgramData/RiskManagerV34")

    if not base_dir.exists():
        print("  ℹ️  No data directory found")
        return

    # Ask for confirmation
    print(f"\n⚠️  WARNING: This will delete all data in {base_dir}")
    print("  This includes:")
    print("    - Configuration files (risk_config.yaml, accounts.yaml)")
    print("    - Log files")
    print("    - Database files")
    print("    - All trading history and state")

    response = input("\n  Are you sure you want to delete all data? (yes/no): ")

    if response.lower() != "yes":
        print("  ℹ️  Keeping data files")
        return

    try:
        shutil.rmtree(base_dir)
        print(f"  ✅ Removed: {base_dir}")

    except Exception as e:
        print(f"  ❌ Failed to remove data: {e}")


def validate_uninstallation() -> None:
    """Validate service uninstallation."""
    print("\n✅ Validating uninstallation...")

    try:
        from risk_manager.daemon.service import RiskManagerService

        # Try to query service (should fail)
        win32serviceutil.QueryServiceStatus(RiskManagerService._svc_name_)

        # If we get here, service still exists
        print(f"  ⚠️  Warning: Service still exists: {RiskManagerService._svc_name_}")
        return False

    except Exception:
        # Service doesn't exist - good!
        print("  ✅ Service successfully removed")
        return True


def print_completion_message(keep_data: bool) -> None:
    """Print completion message."""
    print("\n" + "=" * 70)
    print("🎉 UNINSTALLATION COMPLETE!")
    print("=" * 70)

    if keep_data:
        print("\n📁 Data files preserved:")
        print("   Location: C:\\ProgramData\\RiskManagerV34")
        print("\n   To completely remove all data, run:")
        print("   python uninstall_service.py")

    else:
        print("\n✅ Service and all data removed")

    print("\n" + "=" * 70)


def main():
    """Main uninstallation routine."""
    print("=" * 70)
    print("Risk Manager V34 - Windows Service Uninstallation")
    print("=" * 70)

    # Parse arguments
    parser = argparse.ArgumentParser(description="Uninstall Risk Manager V34 Windows Service")
    parser.add_argument(
        "--keep-data",
        action="store_true",
        help="Keep configuration and data files (only remove service)",
    )

    args = parser.parse_args()

    # Check admin privileges
    if not is_admin():
        print("\n❌ ERROR: This script requires Administrator privileges")
        print("\nPlease:")
        print("  1. Right-click on Command Prompt or PowerShell")
        print("  2. Select 'Run as Administrator'")
        print("  3. Run this script again")
        print("\nPress Enter to exit...")
        input()
        sys.exit(1)

    print("\n✅ Running with Administrator privileges")

    try:
        # Uninstallation steps
        stop_service()
        uninstall_service()
        remove_data(keep_data=args.keep_data)

        # Validate
        validate_uninstallation()

        # Success
        print_completion_message(keep_data=args.keep_data)

    except KeyboardInterrupt:
        print("\n\n⚠️  Uninstallation cancelled by user")
        sys.exit(1)

    except Exception as e:
        print(f"\n\n❌ Uninstallation failed: {e}")
        import traceback

        traceback.print_exc()
        print("\nPress Enter to exit...")
        input()
        sys.exit(1)

    print("\nPress Enter to exit...")
    input()


if __name__ == "__main__":
    main()
