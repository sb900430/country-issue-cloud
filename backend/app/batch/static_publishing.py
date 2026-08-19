import json
from collections.abc import Callable
from pathlib import Path
from shutil import copy2
from typing import Any, Protocol


class DatedResult(Protocol):
    @property
    def date(self) -> object: ...


def publish_static_history[ResultT: DatedResult](
    published_dir: Path,
    site_data_dir: Path,
    dated_pattern: str,
    validate: Callable[[Path], ResultT],
    orphan_message: str,
    extra_files: Callable[[ResultT, list[ResultT]], dict[str, Any]] | None = None,
) -> list[Path]:
    latest_source = published_dir / "latest.json"
    latest = validate(latest_source)
    dated_sources = sorted(published_dir.glob(dated_pattern))[-7:]
    validated = [(source, validate(source)) for source in dated_sources]
    if latest.date not in {result.date for _, result in validated}:
        matching = []
        for source in published_dir.glob(dated_pattern):
            result = validate(source)
            if result.date == latest.date:
                matching.append((source, result))
                break
        if not matching:
            raise ValueError(orphan_message)
        validated = sorted(
            [matching[0], *validated[-6:]], key=lambda item: str(item[1].date)
        )

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
    if extra_files is not None:
        for name, payload in extra_files(latest, [result for _, result in validated]).items():
            (temporary / name).write_text(
                json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            outputs.append(site_data_dir / name)
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
