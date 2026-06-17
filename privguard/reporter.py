from pathlib import Path


def generate_report(profile: dict, output_dir: Path, db_path: Path | None = None) -> Path:
    return output_dir / f"privguard_{profile.get('display_name', 'report')}.xlsx"
