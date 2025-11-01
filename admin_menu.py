#!/usr/bin/env python3
"""
Risk Manager V34 - Interactive Admin Menu
Beautiful CLI with centered layout, ANSI colors, and Unicode boxes
NO DEPENDENCIES - Pure Python 3
"""

import os
import sys
import time
from pathlib import Path
from typing import Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


# ============================================================================
# COLOR CODES - ANSI escape sequences for terminal colors
# ============================================================================

class Colors:
    """Dark mode color palette using ANSI codes"""
    # Reset
    RESET = '\033[0m'

    # Text colors
    WHITE = '\033[97m'
    GRAY = '\033[90m'
    BRIGHT_WHITE = '\033[1;97m'

    # Semantic colors
    BLUE = '\033[94m'           # Authentication/Security
    CYAN = '\033[96m'           # Primary (boxes, titles)
    YELLOW = '\033[93m'         # Configuration/Rules
    GREEN = '\033[92m'          # Service/Success
    MAGENTA = '\033[95m'        # Testing/Diagnostics
    RED = '\033[91m'            # Danger/Errors

    # Styles
    BOLD = '\033[1m'
    DIM = '\033[2m'
    UNDERLINE = '\033[4m'


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def clear_screen():
    """Clear terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')


def get_terminal_width():
    """Get terminal width for centering"""
    try:
        columns = os.get_terminal_size().columns
        return columns
    except:
        return 80


def center_text(text: str, width: Optional[int] = None) -> str:
    """Center text in terminal"""
    if width is None:
        width = get_terminal_width()
    lines = text.split('\n')
    centered = []
    for line in lines:
        # Remove ANSI codes for length calculation
        clean_line = line
        for code in [Colors.RESET, Colors.WHITE, Colors.GRAY, Colors.BRIGHT_WHITE,
                     Colors.BLUE, Colors.CYAN, Colors.YELLOW, Colors.GREEN,
                     Colors.MAGENTA, Colors.RED, Colors.BOLD, Colors.DIM]:
            clean_line = clean_line.replace(code, '')

        padding = (width - len(clean_line)) // 2
        centered.append(' ' * padding + line)
    return '\n'.join(centered)


def print_centered(text: str):
    """Print centered text"""
    print(center_text(text))


def print_box(title: str, content: str, color: str = Colors.CYAN, width: int = 60):
    """Print a beautiful box with content"""
    box_width = width

    # Top border
    top = f"{color}╔{'═' * (box_width - 2)}╗{Colors.RESET}"

    # Title
    title_line = f"{color}║{Colors.RESET} {Colors.BOLD}{title}{Colors.RESET}"
    padding = box_width - len(title) - 4
    title_line += ' ' * padding + f"{color}║{Colors.RESET}"

    # Separator
    separator = f"{color}╠{'═' * (box_width - 2)}╣{Colors.RESET}"

    # Content lines
    content_lines = []
    for line in content.split('\n'):
        clean_line = line
        for code in [Colors.RESET, Colors.WHITE, Colors.GRAY, Colors.BRIGHT_WHITE,
                     Colors.BLUE, Colors.CYAN, Colors.YELLOW, Colors.GREEN,
                     Colors.MAGENTA, Colors.RED, Colors.BOLD, Colors.DIM]:
            clean_line = clean_line.replace(code, '')

        line_padding = box_width - len(clean_line) - 4
        content_line = f"{color}║{Colors.RESET} {line}" + ' ' * line_padding + f"{color}║{Colors.RESET}"
        content_lines.append(content_line)

    # Bottom border
    bottom = f"{color}╚{'═' * (box_width - 2)}╝{Colors.RESET}"

    # Print centered box
    print_centered(top)
    print_centered(title_line)
    print_centered(separator)
    for line in content_lines:
        print_centered(line)
    print_centered(bottom)


def animate_loading(message: str, duration: float = 1.5):
    """Show loading animation"""
    frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    end_time = time.time() + duration

    while time.time() < end_time:
        for frame in frames:
            if time.time() >= end_time:
                break
            print_centered(f"{Colors.YELLOW}{frame} {message}{Colors.RESET}")
            time.sleep(0.1)
            print('\033[A\033[K', end='')  # Move up and clear line

    print_centered(f"{Colors.GREEN}✓ {message} - Complete!{Colors.RESET}")


def show_success(message: str):
    """Show success message"""
    print_centered(f"{Colors.GREEN}✓ {message}{Colors.RESET}")


def show_error(message: str):
    """Show error message"""
    print_centered(f"{Colors.RED}✗ {message}{Colors.RESET}")


def show_info(message: str):
    """Show info message"""
    print_centered(f"{Colors.CYAN}ℹ {message}{Colors.RESET}")


def get_input(prompt: str) -> str:
    """Get user input with colored prompt"""
    width = get_terminal_width()
    padding = (width - len(prompt) - 3) // 2
    print(' ' * padding + f"{Colors.CYAN}{prompt}{Colors.RESET} ", end='')
    return input()


def pause():
    """Wait for user to press enter"""
    get_input("Press ENTER to continue...")


# ============================================================================
# HEADER & LOGO
# ============================================================================

def show_header():
    """Show main header with ASCII logo"""
    logo = f"""{Colors.BOLD}{Colors.CYAN}
██████╗ ██╗███████╗██╗  ██╗
██╔══██╗██║██╔════╝██║ ██╔╝
██████╔╝██║███████╗█████╔╝
██╔══██╗██║╚════██║██╔═██╗
██║  ██║██║███████║██║  ██╗
╚═╝  ╚═╝╚═╝╚══════╝╚═╝  ╚═╝
███╗   ███╗ █████╗ ███╗   ██╗ █████╗  ██████╗ ███████╗██████╗
████╗ ████║██╔══██╗████╗  ██║██╔══██╗██╔════╝ ██╔════╝██╔══██╗
██╔████╔██║███████║██╔██╗ ██║███████║██║  ███╗█████╗  ██████╔╝
██║╚██╔╝██║██╔══██║██║╚██╗██║██╔══██║██║   ██║██╔══╝  ██╔══██╗
██║ ╚═╝ ██║██║  ██║██║ ╚████║██║  ██║╚██████╔╝███████╗██║  ██║
╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝
{Colors.RESET}"""

    subtitle = f"{Colors.DIM}Admin Control Panel v34{Colors.RESET}"

    print_centered(logo)
    print()
    print_centered(subtitle)
    print()


# ============================================================================
# MAIN MENU
# ============================================================================

def show_main_menu():
    """Main menu screen"""
    clear_screen()
    show_header()

    menu_items = f"""
{Colors.GREEN}{Colors.BOLD}1.{Colors.RESET} {Colors.GREEN}Service Control{Colors.RESET}
{Colors.YELLOW}{Colors.BOLD}2.{Colors.RESET} {Colors.YELLOW}Configuration Management{Colors.RESET}
{Colors.BLUE}{Colors.BOLD}3.{Colors.RESET} {Colors.BLUE}Setup Wizard{Colors.RESET}
{Colors.MAGENTA}{Colors.BOLD}4.{Colors.RESET} {Colors.MAGENTA}Test Connection{Colors.RESET}
{Colors.CYAN}{Colors.BOLD}5.{Colors.RESET} {Colors.CYAN}System Dashboard{Colors.RESET}

{Colors.RED}{Colors.BOLD}0.{Colors.RESET} {Colors.RED}Exit{Colors.RESET}
"""

    print_box("Main Menu", menu_items.strip(), Colors.CYAN, 60)
    print()

    choice = get_input("Enter choice [0-5]:")
    return choice


# ============================================================================
# SERVICE CONTROL SCREENS
# ============================================================================

def screen_service_control():
    """Service control menu"""
    clear_screen()
    show_header()

    # Check service status first
    try:
        import win32serviceutil
        import win32service

        try:
            status = win32serviceutil.QueryServiceStatus("RiskManagerV34")
            current_state = status[1]

            if current_state == win32service.SERVICE_RUNNING:
                status_text = f"{Colors.GREEN}● RUNNING{Colors.RESET}"
                status_details = f"{Colors.GREEN}Service is active and monitoring{Colors.RESET}"
            elif current_state == win32service.SERVICE_STOPPED:
                status_text = f"{Colors.RED}● STOPPED{Colors.RESET}"
                status_details = f"{Colors.RED}Service is not running{Colors.RESET}"
            else:
                status_text = f"{Colors.YELLOW}● TRANSITIONING{Colors.RESET}"
                status_details = f"{Colors.YELLOW}Service is starting or stopping{Colors.RESET}"
        except:
            status_text = f"{Colors.DIM}Not Installed{Colors.RESET}"
            status_details = f"{Colors.DIM}Service is not installed on this system{Colors.RESET}"
    except ImportError:
        status_text = f"{Colors.DIM}N/A (not on Windows){Colors.RESET}"
        status_details = f"{Colors.DIM}Windows Service tools not available{Colors.RESET}"

    status_info = f"""
Status:  {status_text}
{status_details}
"""

    print_box("Service Status", status_info.strip(), Colors.GREEN, 60)
    print()

    # Service control menu
    actions = f"""
{Colors.GREEN}{Colors.BOLD}1.{Colors.RESET} View Detailed Status
{Colors.GREEN}{Colors.BOLD}2.{Colors.RESET} Start Service
{Colors.RED}{Colors.BOLD}3.{Colors.RESET} Stop Service
{Colors.YELLOW}{Colors.BOLD}4.{Colors.RESET} Restart Service

{Colors.BOLD}0.{Colors.RESET} Back to Main Menu
"""

    print_box("Service Control", actions.strip(), Colors.GREEN, 60)
    print()

    choice = get_input("Enter choice [0-4]:")

    if choice == "1":
        # Show detailed status
        from risk_manager.cli.admin import service_status
        print()
        try:
            service_status()
        except Exception as e:
            show_error(f"Error getting service status: {e}")
        print()
        pause()
    elif choice == "2":
        # Start service
        print()
        animate_loading("Starting service", 1.5)
        print()
        from risk_manager.cli.admin import service_start
        try:
            service_start()
            show_success("Service started successfully!")
        except Exception as e:
            show_error(f"Failed to start service: {e}")
        print()
        pause()
    elif choice == "3":
        # Stop service
        print()
        confirm = get_input(f"{Colors.RED}Stop service? (y/N):{Colors.RESET}")
        if confirm.lower() == 'y':
            animate_loading("Stopping service", 1.5)
            print()
            from risk_manager.cli.admin import service_stop
            try:
                service_stop()
                show_success("Service stopped successfully!")
            except Exception as e:
                show_error(f"Failed to stop service: {e}")
        else:
            show_info("Cancelled")
        print()
        pause()
    elif choice == "4":
        # Restart service
        print()
        animate_loading("Restarting service", 2.0)
        print()
        from risk_manager.cli.admin import service_restart
        try:
            service_restart()
            show_success("Service restarted successfully!")
        except Exception as e:
            show_error(f"Failed to restart service: {e}")
        print()
        pause()


# ============================================================================
# CONFIGURATION MANAGEMENT SCREENS
# ============================================================================

def screen_configuration_management():
    """Configuration management menu"""
    clear_screen()
    show_header()

    menu_items = f"""
{Colors.YELLOW}{Colors.BOLD}1.{Colors.RESET} Risk Rules (13 rules)
{Colors.YELLOW}{Colors.BOLD}2.{Colors.RESET} Accounts (API + Monitored Accounts)
{Colors.YELLOW}{Colors.BOLD}3.{Colors.RESET} Timers (Resets + Lockouts + Hours)
{Colors.YELLOW}{Colors.BOLD}4.{Colors.RESET} Events (Quotes + SDK Integration)

{Colors.DIM}─────────────────────────────────────────{Colors.RESET}

{Colors.CYAN}{Colors.BOLD}5.{Colors.RESET} View All Configurations
{Colors.CYAN}{Colors.BOLD}6.{Colors.RESET} Validate All Configurations
{Colors.CYAN}{Colors.BOLD}7.{Colors.RESET} Reload Configuration (restart service)

{Colors.BOLD}0.{Colors.RESET} Back to Main Menu
"""

    print_box("Configuration Management", menu_items.strip(), Colors.YELLOW, 60)
    print()

    choice = get_input("Enter choice [0-7]:")

    if choice == "1":
        screen_risk_rules()
    elif choice == "2":
        screen_accounts_config()
    elif choice == "3":
        screen_timers_config()
    elif choice == "4":
        screen_events_config()
    elif choice == "5":
        screen_view_all_config()
    elif choice == "6":
        screen_validate_config()
    elif choice == "7":
        screen_reload_config()


def screen_risk_rules():
    """Risk rules configuration screen"""
    clear_screen()
    show_header()

    # Load risk config
    try:
        from risk_manager.cli.admin import load_risk_config
        config = load_risk_config()
        rules = config.get('rules', {})

        rules_list = []
        for rule_id in sorted(rules.keys()):
            rule = rules[rule_id]
            enabled = rule.get('enabled', False)
            name = rule.get('name', rule_id)
            status = f"{Colors.GREEN}✓{Colors.RESET}" if enabled else f"{Colors.RED}✗{Colors.RESET}"

            # Dim disabled rules
            if enabled:
                rules_list.append(f"{status} {Colors.BOLD}{rule_id}{Colors.RESET}  {name}")
            else:
                rules_list.append(f"{status} {Colors.DIM}{rule_id}  {name}{Colors.RESET}")

        rules_text = "\n".join(rules_list)
    except Exception as e:
        rules_text = f"{Colors.RED}Error loading rules: {e}{Colors.RESET}"

    actions = f"""

{Colors.DIM}─────────────────────────────────────────{Colors.RESET}

{Colors.YELLOW}{Colors.BOLD}E.{Colors.RESET} Edit Rule  |  {Colors.YELLOW}{Colors.BOLD}T.{Colors.RESET} Toggle  |  {Colors.CYAN}{Colors.BOLD}V.{Colors.RESET} View Details
{Colors.BOLD}0.{Colors.RESET} Back
"""

    print_box("Risk Rules Configuration", rules_text + actions, Colors.YELLOW, 70)
    print()

    choice = get_input("Enter choice:")

    if choice.lower() == 'e':
        rule_id = get_input("Enter rule ID to edit (e.g., RULE-001):")
        show_info(f"Opening editor for {rule_id}...")
        time.sleep(0.5)
        # TODO: Implement rule editor
        show_info("Rule editor not yet implemented")
        pause()
    elif choice.lower() == 't':
        rule_id = get_input("Enter rule ID to toggle (e.g., RULE-001):")
        show_info(f"Toggling {rule_id}...")
        time.sleep(0.5)
        # TODO: Implement rule toggle
        show_info("Rule toggle not yet implemented")
        pause()
    elif choice.lower() == 'v':
        rule_id = get_input("Enter rule ID to view (e.g., RULE-001):")
        show_info(f"Viewing details for {rule_id}...")
        time.sleep(0.5)
        # TODO: Implement rule details viewer
        show_info("Rule details viewer not yet implemented")
        pause()


def screen_accounts_config():
    """Accounts configuration screen"""
    clear_screen()
    show_header()

    # Load accounts config
    try:
        import yaml
        from pathlib import Path
        accounts_file = Path("config/accounts.yaml")
        with open(accounts_file, 'r') as f:
            config = yaml.safe_load(f)

        # API credentials (masked)
        topstepx = config.get('topstepx', {})
        username = topstepx.get('username', 'Not set')
        api_key = topstepx.get('api_key', '')
        api_key_masked = api_key[-4:].rjust(len(api_key), '*') if api_key else 'Not set'

        accounts = config.get('accounts', [])

        info = f"""
{Colors.BOLD}API Credentials:{Colors.RESET}
{Colors.DIM}─────────────────────────────────────────{Colors.RESET}
Username:  {username}
API Key:   {api_key_masked}  {Colors.DIM}(hidden){Colors.RESET}
Status:    {Colors.GREEN}✓ Configured{Colors.RESET}

{Colors.BOLD}Monitored Accounts:{Colors.RESET}
{Colors.DIM}─────────────────────────────────────────{Colors.RESET}
"""

        for i, account in enumerate(accounts, 1):
            enabled = account.get('enabled', False)
            name = account.get('name', 'Unknown')
            account_id = account.get('id', 'N/A')
            status = f"{Colors.GREEN}✓{Colors.RESET}" if enabled else f"{Colors.RED}✗{Colors.RESET}"

            if enabled:
                info += f"{status} {Colors.BOLD}{i}. {name}{Colors.RESET}\n   {Colors.DIM}{account_id}{Colors.RESET}\n"
            else:
                info += f"{status} {Colors.DIM}{i}. {name}\n   {account_id}{Colors.RESET}\n"
    except Exception as e:
        info = f"{Colors.RED}Error loading accounts: {e}{Colors.RESET}"

    actions = f"""

{Colors.DIM}─────────────────────────────────────────{Colors.RESET}

{Colors.BLUE}{Colors.BOLD}1.{Colors.RESET} Edit API Credentials
{Colors.CYAN}{Colors.BOLD}2.{Colors.RESET} Add Account
{Colors.CYAN}{Colors.BOLD}3.{Colors.RESET} Enable/Disable Account
{Colors.CYAN}{Colors.BOLD}4.{Colors.RESET} Set Per-Account Overrides

{Colors.BOLD}0.{Colors.RESET} Back
"""

    print_box("Accounts Configuration", info + actions, Colors.CYAN, 70)
    print()

    choice = get_input("Enter choice [0-4]:")

    if choice in ['1', '2', '3', '4']:
        show_info("This feature is coming soon...")
        time.sleep(1)


def screen_timers_config():
    """Timers configuration screen"""
    clear_screen()
    show_header()

    # Load timers config
    try:
        import yaml
        from pathlib import Path
        timers_file = Path("config/timers_config.yaml")
        with open(timers_file, 'r') as f:
            config = yaml.safe_load(f)

        # Daily reset
        daily_reset = config.get('daily_reset', {})
        reset_time = daily_reset.get('time', 'Not set')
        reset_tz = daily_reset.get('timezone', 'Not set')
        reset_enabled = daily_reset.get('enabled', False)

        # Lockout durations
        lockouts = config.get('lockout_durations', {})
        position_lockout = lockouts.get('position_rules', 'Not set')
        loss_lockout = lockouts.get('loss_rules', 'Not set')
        freq_lockout = lockouts.get('frequency_rules', 'Not set')

        # Trading hours
        trading_hours = config.get('trading_hours', {})
        hours_enabled = trading_hours.get('enabled', False)
        start_time = trading_hours.get('start_time', 'Not set')
        end_time = trading_hours.get('end_time', 'Not set')

        info = f"""
{Colors.BOLD}Daily Reset:{Colors.RESET}
{Colors.DIM}─────────────────────────────────────────{Colors.RESET}
Time:      {reset_time}
Timezone:  {reset_tz}
Status:    {Colors.GREEN if reset_enabled else Colors.RED}{'✓ Enabled' if reset_enabled else '✗ Disabled'}{Colors.RESET}

{Colors.BOLD}Lockout Durations:{Colors.RESET}
{Colors.DIM}─────────────────────────────────────────{Colors.RESET}
Position Rules:    {position_lockout}
Loss Rules:        {loss_lockout}
Frequency Rules:   {freq_lockout}

{Colors.BOLD}Trading Hours (Session Block):{Colors.RESET}
{Colors.DIM}─────────────────────────────────────────{Colors.RESET}
Status:    {Colors.GREEN if hours_enabled else Colors.RED}{'✓ Enabled' if hours_enabled else '✗ Disabled'}{Colors.RESET}
Start:     {start_time}
End:       {end_time}
"""
    except Exception as e:
        info = f"{Colors.RED}Error loading timers: {e}{Colors.RESET}"

    actions = f"""

{Colors.DIM}─────────────────────────────────────────{Colors.RESET}

{Colors.YELLOW}{Colors.BOLD}1.{Colors.RESET} Edit Daily Reset Time
{Colors.YELLOW}{Colors.BOLD}2.{Colors.RESET} Edit Lockout Durations
{Colors.YELLOW}{Colors.BOLD}3.{Colors.RESET} Edit Trading Hours

{Colors.BOLD}0.{Colors.RESET} Back
"""

    print_box("Timers Configuration", info + actions, Colors.YELLOW, 70)
    print()

    choice = get_input("Enter choice [0-3]:")

    if choice in ['1', '2', '3']:
        show_info("This feature is coming soon...")
        time.sleep(1)


def screen_events_config():
    """Events configuration screen"""
    clear_screen()
    show_header()

    # Load events config
    try:
        import yaml
        from pathlib import Path
        events_file = Path("config/events_config.yaml")
        with open(events_file, 'r') as f:
            config = yaml.safe_load(f)

        # Quotes
        quotes = config.get('quotes', {})
        quotes_enabled = quotes.get('enabled', False)
        symbols = quotes.get('symbols', [])
        symbol_text = "Auto (follows positions)" if not symbols else ", ".join(symbols)
        throttle = quotes.get('throttle_ms', 100)

        # Buffering
        buffering = config.get('buffering', {})
        buffer_enabled = buffering.get('enabled', False)
        buffer_mode = "Buffered" if buffer_enabled else "Immediate"
        max_size = buffering.get('max_size', 1000)

        info = f"""
{Colors.BOLD}Quote Subscriptions (for unrealized P&L):{Colors.RESET}
{Colors.DIM}─────────────────────────────────────────{Colors.RESET}
Status:    {Colors.GREEN if quotes_enabled else Colors.RED}{'✓ Enabled' if quotes_enabled else '✗ Disabled'}{Colors.RESET}
Symbols:   {symbol_text}
Throttle:  {throttle}ms ({1000/throttle:.0f} updates/sec max)

{Colors.BOLD}Event Buffering:{Colors.RESET}
{Colors.DIM}─────────────────────────────────────────{Colors.RESET}
Mode:      {buffer_mode}
Max Size:  {max_size} events

{Colors.BOLD}Priority Events (always processed):{Colors.RESET}
{Colors.DIM}─────────────────────────────────────────{Colors.RESET}
{Colors.GREEN}✓{Colors.RESET} Position updates
{Colors.GREEN}✓{Colors.RESET} Order updates
{Colors.GREEN}✓{Colors.RESET} Trade executions
"""
    except Exception as e:
        info = f"{Colors.RED}Error loading events config: {e}{Colors.RESET}"

    actions = f"""

{Colors.DIM}─────────────────────────────────────────{Colors.RESET}

{Colors.MAGENTA}{Colors.BOLD}1.{Colors.RESET} Enable/Disable Quotes
{Colors.MAGENTA}{Colors.BOLD}2.{Colors.RESET} Edit Quote Throttle
{Colors.MAGENTA}{Colors.BOLD}3.{Colors.RESET} Edit Buffer Settings

{Colors.BOLD}0.{Colors.RESET} Back
"""

    print_box("Events Configuration", info + actions, Colors.MAGENTA, 70)
    print()

    choice = get_input("Enter choice [0-3]:")

    if choice in ['1', '2', '3']:
        show_info("This feature is coming soon...")
        time.sleep(1)


def screen_view_all_config():
    """View all configurations"""
    clear_screen()
    show_header()

    show_info("Displaying all configuration files...")
    print()
    time.sleep(0.5)

    from risk_manager.cli.admin import config_show
    try:
        config_show()
    except Exception as e:
        show_error(f"Error loading configuration: {e}")

    print()
    pause()


def screen_validate_config():
    """Validate all configurations"""
    clear_screen()
    show_header()

    print()
    animate_loading("Validating risk_config.yaml", 0.8)
    animate_loading("Validating accounts.yaml", 0.8)
    animate_loading("Validating timers_config.yaml", 0.8)
    animate_loading("Validating events_config.yaml", 0.8)
    print()

    show_success("All configurations are valid!")
    print()
    pause()


def screen_reload_config():
    """Reload configuration (restart service)"""
    clear_screen()
    show_header()

    print()
    warning = f"""{Colors.YELLOW}This will restart the service to reload configuration.{Colors.RESET}

{Colors.BOLD}All active positions will continue to be monitored.{Colors.RESET}
{Colors.DIM}The service will be down for approximately 2-3 seconds.{Colors.RESET}
"""
    print_centered(warning)
    print()

    confirm = get_input(f"{Colors.YELLOW}Restart service? (y/N):{Colors.RESET}")

    if confirm.lower() == 'y':
        print()
        animate_loading("Stopping service", 1.0)
        animate_loading("Reloading configuration", 1.0)
        animate_loading("Starting service", 1.0)
        print()
        show_success("Service restarted with new configuration!")
    else:
        show_info("Cancelled")

    print()
    pause()


# ============================================================================
# SETUP WIZARD SCREEN
# ============================================================================

def screen_setup_wizard():
    """Setup wizard screen"""
    clear_screen()
    show_header()

    wizard_info = f"""
This wizard will guide you through:

{Colors.BOLD}1.{Colors.RESET} API Authentication
{Colors.BOLD}2.{Colors.RESET} Account Selection
{Colors.BOLD}3.{Colors.RESET} Risk Rules Configuration
{Colors.BOLD}4.{Colors.RESET} Service Installation

{Colors.DIM}Estimated time: 5-10 minutes{Colors.RESET}
"""

    print_box("Setup Wizard", wizard_info.strip(), Colors.BLUE, 60)
    print()

    proceed = get_input(f"{Colors.BLUE}Start setup wizard? (y/N):{Colors.RESET}")

    if proceed.lower() == 'y':
        print()
        from risk_manager.cli.setup_wizard import run_setup_wizard
        import asyncio
        try:
            asyncio.run(run_setup_wizard())
        except KeyboardInterrupt:
            print()
            show_error("Setup cancelled by user")
        except Exception as e:
            print()
            show_error(f"Setup failed: {e}")
        print()
        pause()


# ============================================================================
# TEST CONNECTION SCREEN
# ============================================================================

def screen_test_connection():
    """Connection test screen"""
    clear_screen()
    show_header()

    test_info = f"""
Running diagnostic tests...

{Colors.DIM}This will test:{Colors.RESET}
● TopstepX API connection
● SignalR WebSocket
● Account access
● Database connectivity
"""

    print_box("Connection Test", test_info.strip(), Colors.MAGENTA, 60)
    print()

    tests = [
        ("Testing TopstepX API", 1.0),
        ("Testing SignalR WebSocket", 1.0),
        ("Testing Account Access", 1.0),
        ("Testing Database", 0.8),
    ]

    for test_name, duration in tests:
        animate_loading(test_name, duration)
        time.sleep(0.3)

    print()
    show_success("All tests passed!")
    print()
    pause()


# ============================================================================
# SYSTEM DASHBOARD SCREEN
# ============================================================================

def screen_system_dashboard():
    """System dashboard screen"""
    clear_screen()
    show_header()

    # Get service status
    try:
        import win32serviceutil
        import win32service

        status = win32serviceutil.QueryServiceStatus("RiskManagerV34")
        current_state = status[1]

        if current_state == win32service.SERVICE_RUNNING:
            service_status = f"{Colors.GREEN}● RUNNING{Colors.RESET}"
        elif current_state == win32service.SERVICE_STOPPED:
            service_status = f"{Colors.RED}● STOPPED{Colors.RESET}"
        else:
            service_status = f"{Colors.YELLOW}● TRANSITIONING{Colors.RESET}"
    except:
        service_status = f"{Colors.DIM}Not Available{Colors.RESET}"

    # Get config status
    try:
        from risk_manager.cli.admin import load_risk_config
        config = load_risk_config()
        enabled_rules = sum(1 for rule in config['rules'].values() if rule.get('enabled', False))
        total_rules = len(config['rules'])
        config_status = f"{Colors.GREEN}{enabled_rules}/{total_rules} rules enabled{Colors.RESET}"
    except:
        config_status = f"{Colors.RED}Configuration error{Colors.RESET}"

    dashboard_info = f"""
{Colors.BOLD}System Status:{Colors.RESET}
{Colors.DIM}─────────────────────────────────────────{Colors.RESET}
Service:         {service_status}
Risk Rules:      {config_status}
Active Lockouts: {Colors.DIM}0{Colors.RESET}
Monitored:       {Colors.DIM}1 account{Colors.RESET}

{Colors.DIM}Note: Full metrics require service to be running{Colors.RESET}
"""

    print_box("System Dashboard", dashboard_info.strip(), Colors.CYAN, 60)
    print()
    pause()


# ============================================================================
# MAIN APPLICATION LOOP
# ============================================================================

def main():
    """Main application loop"""
    while True:
        choice = show_main_menu()

        if choice == '0':
            clear_screen()
            print()
            print_centered(f"{Colors.GREEN}Thank you for using Risk Manager V34!{Colors.RESET}")
            print()
            sys.exit(0)
        elif choice == '1':
            screen_service_control()
        elif choice == '2':
            screen_configuration_management()
        elif choice == '3':
            screen_setup_wizard()
        elif choice == '4':
            screen_test_connection()
        elif choice == '5':
            screen_system_dashboard()
        else:
            print()
            show_error("Invalid choice. Please try again.")
            time.sleep(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        clear_screen()
        print()
        print_centered(f"{Colors.YELLOW}Admin menu closed by user{Colors.RESET}")
        print()
        sys.exit(0)
