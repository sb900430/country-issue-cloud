import json
from collections.abc import Callable
from pathlib import Path
from shutil import copy2
from typing import Protocol


class DatedResult(Protocol):
    @property
    def date(self) -> object: ...


def publish_static_history(
    published_dir: Path,
    site_data_dir: Path,
    dated_pattern: str,
    validate: Callable[[Path], DatedResult],
    orphan_message: str,
) -> list[Path]:
    latest_source = published_dir / "latest.json"
    latest = validate(latest_source)
    dated_sources = sorted(published_dir.glob(dated_pattern))[-7:]
    validated = [(source, validate(source)) for source in dated_sources]
    if latest.date not in {result.date for _, result in validated}:
        raise ValueError(orphan_message)

    temporary = site_data_dir.with_name(f".{site_data_dir.name}.tmp")
    _empty_directory(temporary)
    outputs = [site_data_dir / "latest.json"]
    copy2(latest_source, temporary / "latest.json")
    for source, result in validated:
        destination = temporary / f"{result.date}.json"
        copy2(source, destination)
        outputs.append(site_data_dir / destination.name)

    dates = [str(result.date) for _, result in reversed(validated)]
    (temporary / "dates.json").write_text(
        json.dumps(dates, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    outputs.append(site_data_dir / "dates.json")
    _replace_directory(temporary, site_data_dir)
    return outputs


def _empty_directory(path: Path) -> None:
    if path.exists():
        for child in path.iterdir():
            child.unlink()
    path.mkdir(parents=True, exist_ok=True)


def _replace_directory(temporary: Path, destination: Path) -> None:
    if not destination.exists():
        temporary.replace(destination)
        return

    backup = destination.with_name(f".{destination.name}.previous")
    if backup.exists():
        for path in backup.iterdir():
            path.unlink()
        backup.rmdir()
    destination.replace(backup)
    try:
        temporary.replace(destination)
    except OSError:
        backup.replace(destination)
        raise
    for path in backup.iterdir():
        path.unlink()
    backup.rmdir()
