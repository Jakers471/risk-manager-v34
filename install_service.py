"""
Install Risk Manager V34 Windows Service.

This script installs the Risk Manager as a Windows Service with
LocalSystem privileges for maximum protection.

Requirements:
    - Must be run with Administrator privileges (UAC prompt)
    - Python 3.12+ installed
    - pywin32 package installed (pip install pywin32)

Usage:
    Right-click terminal → "Run as Administrator"
    python install_service.py
"""

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


def create_directories() -> None:
    """Create required directories for service."""
    print("\n📁 Creating directories...")

    base_dir = Path("C:/ProgramData/RiskManagerV34")

    directories = [
        base_dir / "config",
        base_dir / "data",
        base_dir / "data" / "logs",
        base_dir / "data" / "database",
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"  ✅ Created: {directory}")


def copy_config_files() -> None:
    """Copy configuration files to ProgramData."""
    print("\n📋 Copying configuration files...")

    project_dir = Path(__file__).parent
    config_source = project_dir / "config"
    config_dest = Path("C:/ProgramData/RiskManagerV34/config")

    # Copy risk_config.yaml or template
    risk_config_source = config_source / "risk_config.yaml"

    if not risk_config_source.exists():
        risk_config_source = config_source / "risk_config.yaml.template"

    if risk_config_source.exists():
        risk_config_dest = config_dest / "risk_config.yaml"
        shutil.copy2(risk_config_source, risk_config_dest)
        print(f"  ✅ Copied: {risk_config_source.name} → {risk_config_dest}")

    else:
        print("  ⚠️  Warning: risk_config.yaml not found")

    # Copy accounts.yaml or template
    accounts_source = config_source / "accounts.yaml"

    if not accounts_source.exists():
        accounts_source = config_source / "accounts.yaml.template"

    if accounts_source.exists():
        accounts_dest = config_dest / "accounts.yaml"
        shutil.copy2(accounts_source, accounts_dest)
        print(f"  ✅ Copied: {accounts_source.name} → {accounts_dest}")

    else:
        print("  ⚠️  Warning: accounts.yaml not found")


def install_service() -> None:
    """Install Windows Service."""
    print("\n🔧 Installing Windows Service...")

    try:
        # Import service class
        from risk_manager.daemon.service import RiskManagerService

        # Install service
        win32serviceutil.InstallService(
            pythonClassString="risk_manager.daemon.service.RiskManagerService",
            serviceName=RiskManagerService._svc_name_,
            displayName=RiskManagerService._svc_display_name_,
            description=RiskManagerService._svc_description_,
            startType=win32service.SERVICE_AUTO_START,
        )

        print(f"  ✅ Service installed: {RiskManagerService._svc_name_}")

        # Configure service recovery options (restart on failure)
        configure_service_recovery()

    except Exception as e:
        print(f"  ❌ Service installation failed: {e}")
        raise


def configure_service_recovery() -> None:
    """
    Configure service recovery options.

    Sets service to automatically restart on failure:
        - First failure: Restart after 1 minute
        - Second failure: Restart after 1 minute
        - Subsequent failures: Restart after 1 minute
    """
    print("\n🔄 Configuring service recovery...")

    try:
        import subprocess

        # Use sc.exe to configure failure actions
        service_name = "RiskManagerV34"

        # Set failure actions: restart service after 60 seconds (60000 ms)
        cmd = [
            "sc",
            "failure",
            service_name,
            "reset=",
            "86400",  # Reset failure count after 24 hours
            "actions=",
            "restart/60000/restart/60000/restart/60000",
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, check=False)

        if result.returncode == 0:
            print("  ✅ Recovery options configured (restart on failure)")
        else:
            print(f"  ⚠️  Warning: Failed to configure recovery: {result.stderr}")

    except Exception as e:
        print(f"  ⚠️  Warning: Failed to configure recovery: {e}")


def validate_installation() -> None:
    """Validate service installation."""
    print("\n✅ Validating installation...")

    try:
        from risk_manager.daemon.service import RiskManagerService

        # Check if service exists
        status = win32serviceutil.QueryServiceStatus(RiskManagerService._svc_name_)

        # Status codes:
        # 1 = STOPPED
        # 2 = START_PENDING
        # 3 = STOP_PENDING
        # 4 = RUNNING

        status_map = {
            win32service.SERVICE_STOPPED: "Stopped",
            win32service.SERVICE_START_PENDING: "Starting",
            win32service.SERVICE_STOP_PENDING: "Stopping",
            win32service.SERVICE_RUNNING: "Running",
        }

        current_status = status_map.get(status[1], "Unknown")

        print(f"  ✅ Service status: {current_status}")
        print(f"  ✅ Service name: {RiskManagerService._svc_name_}")
        print(f"  ✅ Display name: {RiskManagerService._svc_display_name_}")

        return True

    except Exception as e:
        print(f"  ❌ Validation failed: {e}")
        return False


def print_next_steps() -> None:
    """Print next steps for user."""
    print("\n" + "=" * 70)
    print("🎉 INSTALLATION COMPLETE!")
    print("=" * 70)

    print("\n📝 Next Steps:")
    print("\n1. Configure the service:")
    print("   - Edit: C:\\ProgramData\\RiskManagerV34\\config\\risk_config.yaml")
    print("   - Edit: C:\\ProgramData\\RiskManagerV34\\config\\accounts.yaml")
    print("   - Set your TopstepX credentials and risk limits")

    print("\n2. Start the service:")
    print("   - Option A: services.msc → Find 'Risk Manager V34' → Right-click → Start")
    print("   - Option B: net start RiskManagerV34")
    print("   - Option C: sc start RiskManagerV34")

    print("\n3. Verify service is running:")
    print("   - Check Windows Services (services.msc)")
    print("   - View logs: C:\\ProgramData\\RiskManagerV34\\data\\logs\\risk_manager.log")
    print("   - Check Windows Event Viewer → Application")

    print("\n4. Monitor service:")
    print("   - Service will auto-start on system boot")
    print("   - Service will auto-restart on failure")
    print("   - Requires Windows admin password to stop")

    print("\n⚠️  IMPORTANT SECURITY:")
    print("   - Service runs as LocalSystem (highest privilege)")
    print("   - Trader CANNOT stop service without Windows admin password")
    print("   - Configuration files protected by Windows ACL")
    print("   - Only Windows admin can modify service")

    print("\n📚 Documentation:")
    print("   - Installation guide: docs/deployment/WINDOWS_SERVICE.md")
    print("   - Configuration guide: docs/current/CONFIG_FORMATS.md")
    print("   - Security model: docs/current/SECURITY_MODEL.md")

    print("\n" + "=" * 70)


def main():
    """Main installation routine."""
    print("=" * 70)
    print("Risk Manager V34 - Windows Service Installation")
    print("=" * 70)

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
        # Installation steps
        create_directories()
        copy_config_files()
        install_service()

        # Validate
        if not validate_installation():
            print("\n❌ Installation validation failed")
            sys.exit(1)

        # Success
        print_next_steps()

    except KeyboardInterrupt:
        print("\n\n⚠️  Installation cancelled by user")
        sys.exit(1)

    except Exception as e:
        print(f"\n\n❌ Installation failed: {e}")
        import traceback

        traceback.print_exc()
        print("\nPress Enter to exit...")
        input()
        sys.exit(1)

    print("\nPress Enter to exit...")
    input()


if __name__ == "__main__":
    main()
