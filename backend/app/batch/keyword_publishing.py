import json
from pathlib import Path
from shutil import copy2

from app.schemas.keywords import KeywordResult


class KeywordStaticJsonPublisher:
    def __init__(self, published_dir: Path, site_data_dir: Path) -> None:
        self.published_dir = published_dir
        self.site_data_dir = site_data_dir

    def publish(self) -> list[Path]:
        latest_source = self.published_dir / "latest.json"
        latest = self._validate(latest_source)
        dated_sources = sorted(self.published_dir.glob("keywords_????-??-??.json"))[-7:]
        validated = [(source, self._validate(source)) for source in dated_sources]
        if latest.date not in {result.date for _, result in validated}:
            raise ValueError("latest keyword result has no matching dated result")
        temporary = self.site_data_dir.with_name(f".{self.site_data_dir.name}.tmp")
        if temporary.exists():
            for path in temporary.iterdir():
                path.unlink()
        temporary.mkdir(parents=True, exist_ok=True)
        copy2(latest_source, temporary / "latest.json")
        outputs = [self.site_data_dir / "latest.json"]
        for source, result in validated:
            destination = temporary / f"{result.date.isoformat()}.json"
            copy2(source, destination)
            outputs.append(self.site_data_dir / destination.name)
        dates = [result.date.isoformat() for _, result in reversed(validated)]
        (temporary / "dates.json").write_text(
            json.dumps(dates, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        outputs.append(self.site_data_dir / "dates.json")
        if self.site_data_dir.exists():
            backup = self.site_data_dir.with_name(f".{self.site_data_dir.name}.previous")
            if backup.exists():
                for path in backup.iterdir():
                    path.unlink()
                backup.rmdir()
            self.site_data_dir.replace(backup)
            try:
                temporary.replace(self.site_data_dir)
            except OSError:
                backup.replace(self.site_data_dir)
                raise
            for path in backup.iterdir():
                path.unlink()
            backup.rmdir()
        else:
            temporary.replace(self.site_data_dir)
        return outputs

    @staticmethod
    def _validate(path: Path) -> KeywordResult:
        return KeywordResult.model_validate_json(path.read_text(encoding="utf-8"))
