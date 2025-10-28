"""
Demo script to showcase the enhanced Service Control Panel visuals.

This demonstrates the Rich-based visual output without requiring
the actual Windows Service to be installed.
"""

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich import box

console = Console()


def demo_service_start():
    """Demo: Service start command output."""
    console.print("\n[bold cyan]Command:[/bold cyan] admin_cli service start\n")

    # Starting panel
    panel_content = Text()
    panel_content.append("> Starting Risk Manager...\n\n", style="yellow")

    panel = Panel(
        panel_content,
        title="STARTING SERVICE",
        box=box.DOUBLE,
        border_style="cyan",
        expand=False
    )
    console.print(panel)

    # Success panel
    success_content = Text()
    success_content.append("[OK] Service started", style="bold green")
    success_content.append(" (PID: 12345)", style="dim")
    success_content.append("\n[OK] Monitoring account: ", style="green")
    success_content.append("PRAC-V2-126244", style="cyan bold")
    success_content.append(f"\n[OK] Active rules: ", style="green")
    success_content.append("10/13 enabled", style="cyan bold")
    success_content.append("\n[OK] SDK connected\n\n", style="green")
    success_content.append("Service is now running [OK]", style="bold green")

    console.print()
    console.print(Panel(
        success_content,
        title="SERVICE STARTED",
        box=box.DOUBLE,
        border_style="green",
        expand=False
    ))


def demo_service_stop():
    """Demo: Service stop command output."""
    console.print("\n\n[bold cyan]Command:[/bold cyan] admin_cli service stop\n")

    # Warning panel
    warning_panel = Panel(
        "[bold yellow]! WARNING[/bold yellow]\n\n"
        "Stopping the service will:\n"
        "- Disable all risk enforcement\n"
        "- Stop monitoring your account\n"
        "- Allow unrestricted trading\n\n"
        "[bold]This removes all trading protections![/bold]",
        title="Confirm Stop",
        box=box.DOUBLE,
        border_style="yellow",
        expand=False
    )
    console.print(warning_panel)

    console.print("\n[dim]User confirms: Yes[/dim]\n")

    # Stopping panel
    panel_content = Text()
    panel_content.append("> Stopping Risk Manager...\n", style="yellow")

    panel = Panel(
        panel_content,
        title="STOPPING SERVICE",
        box=box.DOUBLE,
        border_style="cyan",
        expand=False
    )
    console.print(panel)

    # Success panel
    success_content = Text()
    success_content.append("[OK] Service stopped", style="bold green")
    success_content.append(" (PID: 12345)", style="dim")
    success_content.append("\n[!] Risk enforcement DISABLED\n\n", style="bold red")
    success_content.append("Trading protection is now OFF. Use ", style="dim")
    success_content.append("admin_cli service start", style="cyan")
    success_content.append(" to re-enable.", style="dim")

    console.print()
    console.print(Panel(
        success_content,
        title="SERVICE STOPPED",
        box=box.DOUBLE,
        border_style="yellow",
        expand=False
    ))


def demo_service_restart():
    """Demo: Service restart command output."""
    console.print("\n\n[bold cyan]Command:[/bold cyan] admin_cli service restart\n")

    panel = Panel(
        "> Restarting Risk Manager...\n",
        title="RESTARTING SERVICE",
        box=box.DOUBLE,
        border_style="cyan",
        expand=False
    )
    console.print(panel)

    # Progress content
    progress_content = Text()
    progress_content.append("> Stopping service...\n", style="yellow")
    progress_content.append("[OK] Stopped", style="green")
    progress_content.append(" (PID: 12345)", style="dim")
    progress_content.append("\n", style="")
    progress_content.append("> Starting service...\n", style="yellow")
    progress_content.append("[OK] Started", style="green")
    progress_content.append(" (PID: 67890)", style="dim")
    progress_content.append("\n", style="")
    progress_content.append("[OK] Configuration reloaded\n\n", style="green")
    progress_content.append("Service restarted successfully [OK]", style="bold green")

    console.print()
    console.print(Panel(
        progress_content,
        title="SERVICE RESTARTED",
        box=box.DOUBLE,
        border_style="green",
        expand=False
    ))


def demo_service_status():
    """Demo: Service status command output."""
    console.print("\n\n[bold cyan]Command:[/bold cyan] admin_cli service status\n")

    # Build status content
    status_content = Text()

    # Service state
    status_content.append("State:         ", style="bold")
    status_content.append("[*] RUNNING", style="bold green")
    status_content.append("\n")

    status_content.append("PID:           12345\n", style="")
    status_content.append("Uptime:        3h 24m 15s\n", style="")
    status_content.append("CPU Usage:     2.3%\n", style="")
    status_content.append("Memory:        45.2 MB\n", style="")
    status_content.append("\n")

    # Connection status
    status_content.append("CONNECTION STATUS\n", style="bold")
    status_content.append("--------------\n", style="dim")
    status_content.append("TopstepX API:    [OK] Connected", style="green")
    status_content.append(" (45ms)\n", style="dim")
    status_content.append("SDK:             [OK] Connected", style="green")
    status_content.append(" (32ms)\n", style="dim")
    status_content.append("Database:        [OK] OK\n", style="green")
    status_content.append("\n")

    # Monitoring status
    status_content.append("MONITORING\n", style="bold")
    status_content.append("--------------\n", style="dim")
    status_content.append("Account:         ", style="")
    status_content.append("PRAC-V2-126244\n", style="cyan")
    status_content.append("Enabled Rules:   10/13\n", style="")
    status_content.append("Active Lockouts: 0\n", style="")
    status_content.append("Events Today:    142\n", style="")

    # Create panel
    panel = Panel(
        status_content,
        title="SERVICE STATUS",
        box=box.DOUBLE,
        border_style="cyan",
        expand=False
    )

    console.print(panel)


def demo_service_not_installed():
    """Demo: Service not installed error."""
    console.print("\n\n[bold cyan]Command:[/bold cyan] admin_cli service status (service not installed)\n")

    console.print(Panel(
        "[bold red]Service not installed![/bold red]\n\n"
        "The Risk Manager service is not installed on this system.\n\n"
        "To install the service, run:\n"
        "[cyan]admin_cli service install[/cyan]",
        title="Error",
        border_style="red",
        expand=False
    ))


def main():
    """Run all demos."""
    console.print("\n")
    console.print(Panel(
        "[bold]Admin CLI - Service Control Panel Visual Enhancements[/bold]\n\n"
        "This demonstrates the Rich-based visual output for service control commands.",
        title="SERVICE CONTROL PANEL - VISUAL DEMO",
        box=box.DOUBLE,
        border_style="bold cyan",
        expand=False
    ))

    # Demo each command
    demo_service_start()
    demo_service_stop()
    demo_service_restart()
    demo_service_status()
    demo_service_not_installed()

    console.print("\n")
    console.print(Panel(
        "[bold green]All visual demos completed successfully![/bold green]\n\n"
        "These visual enhancements are now available in the Admin CLI:\n"
        "- [cyan]admin_cli service start[/cyan]\n"
        "- [cyan]admin_cli service stop[/cyan]\n"
        "- [cyan]admin_cli service restart[/cyan]\n"
        "- [cyan]admin_cli service status[/cyan]",
        title="DEMO COMPLETE",
        box=box.DOUBLE,
        border_style="bold green",
        expand=False
    ))
    console.print()


if __name__ == "__main__":
    main()
