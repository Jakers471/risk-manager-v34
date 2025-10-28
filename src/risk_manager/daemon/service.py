"""
Windows Service implementation for Risk Manager V34.

This module provides the Windows Service wrapper that runs the Risk Manager
as a background service with LocalSystem privileges.
"""

import sys
import traceback
from pathlib import Path

import servicemanager
import win32event
import win32service
import win32serviceutil
from loguru import logger

from risk_manager.daemon.runner import ServiceRunner


class RiskManagerService(win32serviceutil.ServiceFramework):
    """
    Windows Service for Risk Manager V34.

    Runs as background service with LocalSystem privileges, providing
    24/7 trading risk management that cannot be killed by the trader
    without Windows admin password.

    Service Configuration:
        Name: RiskManagerV34
        Display Name: Risk Manager V34 - Trading Protection
        Description: Automated risk management for TopstepX trading accounts
        Start Type: Automatic
        Account: LocalSystem
        Recovery: Restart on failure (3 attempts, 1 min delay)

    Security:
        - Runs as LocalSystem (highest privilege)
        - Cannot be stopped without Windows admin password
        - Configuration files protected by Windows ACL
        - Logs to Windows Event Log and file system
    """

    # Service configuration
    _svc_name_ = "RiskManagerV34"
    _svc_display_name_ = "Risk Manager V34 - Trading Protection"
    _svc_description_ = (
        "Automated risk management for TopstepX trading accounts. "
        "Monitors positions and enforces risk rules in real-time. "
        "Requires Windows admin password to stop or modify."
    )

    def __init__(self, args):
        """
        Initialize Windows Service.

        Args:
            args: Service arguments from Windows Service Manager
        """
        win32serviceutil.ServiceFramework.__init__(self, args)

        # Create stop event for graceful shutdown
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)

        # Service state
        self.running = False
        self.runner: ServiceRunner | None = None

        # Log service initialization
        self._log_info("Service initialized")

    def SvcStop(self):
        """
        Handle service stop request.

        Called by Windows Service Manager when service is stopped.
        Triggers graceful shutdown of Risk Manager.
        """
        self._log_info("Service stop requested")

        # Report stop pending to Service Manager
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)

        # Signal stop event
        win32event.SetEvent(self.stop_event)

        # Set flag
        self.running = False

        self._log_info("Service stopping...")

    def SvcDoRun(self):
        """
        Main service execution entry point.

        Called by Windows Service Manager when service is started.
        Runs the Risk Manager until stop is requested.
        """
        # Log service start to Windows Event Log
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, ""),
        )

        self._log_info("Service starting...")

        try:
            # Run main service loop
            self.main()

        except Exception as e:
            # Log exception to Windows Event Log
            error_msg = f"Service crashed with exception: {e}\n{traceback.format_exc()}"
            self._log_error(error_msg)

            # Log to Windows Event Log
            servicemanager.LogErrorMsg(error_msg)

            # Report stopped status
            self.ReportServiceStatus(win32service.SERVICE_STOPPED)

            raise

        # Log service stop to Windows Event Log
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STOPPED,
            (self._svc_name_, ""),
        )

        self._log_info("Service stopped")

    def main(self):
        """
        Main service loop.

        Initializes and runs the Risk Manager, handles reconnection
        and error recovery.
        """
        self.running = True

        # Determine config path
        config_path = self._get_config_path()

        self._log_info(f"Loading configuration from: {config_path}")

        try:
            # Create service runner
            self.runner = ServiceRunner(config_path=config_path)

            # Start Risk Manager
            self._log_info("Starting Risk Manager...")
            self.runner.start()

            self._log_info("Risk Manager started successfully")

            # Run until stop signal
            while self.running:
                # Wait for stop event (check every 5 seconds)
                rc = win32event.WaitForSingleObject(self.stop_event, 5000)

                if rc == win32event.WAIT_OBJECT_0:
                    # Stop event signaled
                    self._log_info("Stop event signaled")
                    break

                # Check if runner is still healthy
                if self.runner and not self.runner.is_running():
                    self._log_warning("Risk Manager stopped unexpectedly, restarting...")

                    # Attempt restart
                    try:
                        self.runner.restart()
                        self._log_info("Risk Manager restarted successfully")

                    except Exception as e:
                        self._log_error(f"Failed to restart Risk Manager: {e}")

                        # Log error to Windows Event Log
                        servicemanager.LogErrorMsg(
                            f"Failed to restart Risk Manager: {e}\n{traceback.format_exc()}"
                        )

                        # Wait before retrying
                        win32event.WaitForSingleObject(self.stop_event, 60000)  # 1 minute

        except Exception as e:
            self._log_error(f"Service error: {e}\n{traceback.format_exc()}")
            raise

        finally:
            # Graceful shutdown
            self._log_info("Shutting down Risk Manager...")

            if self.runner:
                try:
                    self.runner.stop()
                    self._log_info("Risk Manager stopped gracefully")

                except Exception as e:
                    self._log_error(f"Error during shutdown: {e}")

    def _get_config_path(self) -> Path:
        """
        Get configuration file path.

        Returns:
            Path to risk_config.yaml

        The configuration is stored in ProgramData for system-wide access:
            C:\\ProgramData\\RiskManagerV34\\config\\risk_config.yaml
        """
        # Production config location (ProgramData)
        program_data = Path("C:/ProgramData/RiskManagerV34/config/risk_config.yaml")

        if program_data.exists():
            return program_data

        # Development fallback (project directory)
        project_dir = Path(__file__).parent.parent.parent.parent.parent
        dev_config = project_dir / "config" / "risk_config.yaml"

        if dev_config.exists():
            return dev_config

        # Last resort - use template
        template = project_dir / "config" / "risk_config.yaml.template"

        if template.exists():
            self._log_warning(f"Using config template: {template}")
            return template

        # Error - no config found
        raise FileNotFoundError(
            "Configuration file not found. Please run install_service.py to set up configuration."
        )

    def _log_info(self, message: str):
        """Log info message to Windows Event Log and logger."""
        logger.info(message)

        try:
            servicemanager.LogInfoMsg(f"{self._svc_name_}: {message}")
        except Exception:
            # Ignore logging errors
            pass

    def _log_warning(self, message: str):
        """Log warning message to Windows Event Log and logger."""
        logger.warning(message)

        try:
            servicemanager.LogWarningMsg(f"{self._svc_name_}: {message}")
        except Exception:
            # Ignore logging errors
            pass

    def _log_error(self, message: str):
        """Log error message to Windows Event Log and logger."""
        logger.error(message)

        try:
            servicemanager.LogErrorMsg(f"{self._svc_name_}: {message}")
        except Exception:
            # Ignore logging errors
            pass


def main():
    """
    Service entry point.

    Handles service installation, start, stop, etc. via command line.

    Usage:
        python service.py install    # Install service
        python service.py start      # Start service
        python service.py stop       # Stop service
        python service.py remove     # Uninstall service
        python service.py debug      # Run in debug mode (console)
    """
    if len(sys.argv) == 1:
        # No arguments - run as service
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(RiskManagerService)
        servicemanager.StartServiceCtrlDispatcher()

    else:
        # Arguments provided - handle command line
        win32serviceutil.HandleCommandLine(RiskManagerService)


if __name__ == "__main__":
    main()
