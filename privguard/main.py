from pathlib import Path

import click

from privguard.db import init_db
from privguard.reporter import generate_report
from privguard.scanner import scan_user
from privguard.submitter import submit_removals
from privguard.vault import load_vault, save_vault

VAULT_PATH = Path.home() / ".privguard" / "vault.enc"
DB_PATH = Path.home() / ".privguard" / "privguard.db"


def _prompt_password(prompt: str = "Master password") -> str:
    return click.prompt(prompt, hide_input=True)


def _load_vault_or_exit(password: str) -> dict:
    try:
        return load_vault(password, VAULT_PATH)
    except ValueError:
        raise click.ClickException("Wrong master password.")
    except FileNotFoundError:
        raise click.ClickException("No vault found. Run 'privguard init' first.")


def _filter_users(users: list, name: str | None) -> list:
    if name is None:
        return users
    matched = [u for u in users if u["display_name"] == name]
    if not matched:
        raise click.ClickException(f"User '{name}' not found.")
    return matched


def _collect_list(prompt: str) -> list:
    items: list[str] = []
    while True:
        value = click.prompt(prompt, default="", show_default=False)
        if value == "":
            break
        items.append(value)
    return items


def _collect_addresses() -> list:
    addresses: list[dict] = []
    while True:
        street = click.prompt("Address street (blank to stop)", default="", show_default=False)
        if street == "":
            break
        city = click.prompt("  City")
        state = click.prompt("  State")
        zip_code = click.prompt("  ZIP")
        current = click.confirm("  Is this the current address?", default=True)
        addresses.append({"street": street, "city": city, "state": state, "zip": zip_code, "current": current})
    return addresses


@click.group()
def cli() -> None:
    """PrivGuard — personal PII protection tool."""


@cli.command()
def init() -> None:
    """Create a new encrypted vault and initialise the database."""
    if VAULT_PATH.exists():
        raise click.ClickException(
            f"Vault already exists at {VAULT_PATH}. Remove it manually if you want to start over."
        )

    password = click.prompt(
        "Choose a master password",
        hide_input=True,
        confirmation_prompt="Confirm master password",
    )

    VAULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    empty_vault: dict = {"users": [], "api_keys": {}}
    save_vault(password, empty_vault, VAULT_PATH)
    init_db(DB_PATH)

    click.echo(f"PrivGuard initialized. Vault: {VAULT_PATH}")
    click.echo("Run 'privguard user add' to add your first profile.")


@cli.group()
def user() -> None:
    """Manage user profiles stored in the vault."""


@user.command("add")
def user_add() -> None:
    """Interactively add a new profile to the vault."""
    password = _prompt_password()
    vault = _load_vault_or_exit(password)

    click.echo("\n-- New profile --")
    display_name = click.prompt("Display name")
    full_name = click.prompt("Full legal name")
    date_of_birth = click.prompt("Date of birth (YYYY-MM-DD)")

    click.echo("Emails (enter blank to stop):")
    emails = _collect_list("  Email")

    click.echo("Phone numbers (enter blank to stop):")
    phone_numbers = _collect_list("  Phone")

    click.echo("Addresses (enter blank street to stop):")
    addresses = _collect_addresses()

    click.echo("Aliases / nicknames (enter blank to stop):")
    aliases = _collect_list("  Alias")

    ssn_raw = click.prompt("SSN last 4 digits (blank to skip)", default="", show_default=False)
    ssn_last4: str | None = ssn_raw.strip() or None

    if not vault["api_keys"].get("hibp"):
        hibp_key = click.prompt("HIBP API key")
        vault["api_keys"]["hibp"] = hibp_key

    profile = {
        "display_name": display_name,
        "full_name": full_name,
        "aliases": aliases,
        "date_of_birth": date_of_birth,
        "emails": emails,
        "phone_numbers": phone_numbers,
        "addresses": addresses,
        "ssn_last4": ssn_last4,
    }
    vault["users"].append(profile)
    save_vault(password, vault, VAULT_PATH)
    click.echo(f"\nProfile '{display_name}' added.")


@user.command("list")
def user_list() -> None:
    """List all profiles in the vault."""
    password = _prompt_password()
    vault = _load_vault_or_exit(password)
    users = vault.get("users", [])

    if not users:
        click.echo("No profiles found.")
        return

    click.echo(f"\n{'Name':<30}  {'Emails':>6}  {'Addresses':>9}")
    click.echo("-" * 52)
    for u in users:
        name = u.get("display_name", "(unnamed)")
        email_count = len(u.get("emails", []))
        addr_count = len(u.get("addresses", []))
        click.echo(f"{name:<30}  {email_count:>6}  {addr_count:>9}")


@user.command("remove")
@click.option("--user", "user_name", required=True, help="Display name of the profile to remove.")
def user_remove(user_name: str) -> None:
    """Remove a profile from the vault by display name."""
    password = _prompt_password()
    vault = _load_vault_or_exit(password)

    original_count = len(vault["users"])
    vault["users"] = [u for u in vault["users"] if u["display_name"] != user_name]

    if len(vault["users"]) == original_count:
        raise click.ClickException(f"User '{user_name}' not found.")

    save_vault(password, vault, VAULT_PATH)
    click.echo(f"Profile '{user_name}' removed.")


@cli.command()
@click.option("--user", "user_name", default=None, help="Limit scan to this display name.")
@click.option(
    "--source",
    default=None,
    type=click.Choice(["brokers", "hibp", "social", "search_engines"]),
    help="Limit scan to a specific source.",
)
@click.option("--force", is_flag=True, default=False, help="Re-scan even if recently scanned.")
def scan(user_name: str | None, source: str | None, force: bool) -> None:
    """Scan data brokers, HIBP, social profiles, and search engines."""
    password = _prompt_password()
    vault = _load_vault_or_exit(password)
    users = _filter_users(vault.get("users", []), user_name)
    api_keys = vault.get("api_keys", {})

    for profile in users:
        click.echo(f"Scanning: {profile['display_name']}")
        scan_user(profile, api_keys, source=source, force=force, db_path=DB_PATH)

    click.echo("Scan complete.")


@cli.command()
@click.option("--user", "user_name", default=None, help="Limit to this display name.")
@click.option("--force", is_flag=True, default=False, help="Re-submit even if already submitted.")
def submit(user_name: str | None, force: bool) -> None:
    """Submit opt-out / removal requests to data brokers."""
    password = _prompt_password()
    vault = _load_vault_or_exit(password)
    users = _filter_users(vault.get("users", []), user_name)

    for profile in users:
        click.echo(f"Submitting removals for: {profile['display_name']}")
        submit_removals(profile, force=force, db_path=DB_PATH)

    click.echo("Submissions complete.")


@cli.command()
@click.option("--user", "user_name", default=None, help="Limit to this display name.")
@click.option("--output", "output_dir", default=None, type=click.Path(), help="Directory to write the report.")
def report(user_name: str | None, output_dir: str | None) -> None:
    """Generate an Excel report of scan results and opt-out statuses."""
    password = _prompt_password()
    vault = _load_vault_or_exit(password)
    users = _filter_users(vault.get("users", []), user_name)

    resolved_output = Path(output_dir) if output_dir else Path.cwd()

    for profile in users:
        path = generate_report(profile, resolved_output, db_path=DB_PATH)
        click.echo(f"Report saved: {path}")
