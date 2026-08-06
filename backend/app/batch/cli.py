import argparse
from pathlib import Path

from app.batch.publishing import StaticJsonPublisher
from app.repositories.json_issue_repository import JsonIssueRepository
from app.schemas.issues import IssueResult


def main() -> int:
    parser = argparse.ArgumentParser(prog="country-issue-cloud-batch")
    subparsers = parser.add_subparsers(dest="command", required=True)
    fixture = subparsers.add_parser("publish-fixture")
    fixture.add_argument("--fixture", type=Path, required=True)
    fixture.add_argument("--data-dir", type=Path, required=True)
    fixture.add_argument("--site-data-dir", type=Path, required=True)
    arguments = parser.parse_args()

    if arguments.command == "publish-fixture":
        result = IssueResult.model_validate_json(arguments.fixture.read_text(encoding="utf-8"))
        repository = JsonIssueRepository(arguments.data_dir)
        repository.save(result)
        publisher = StaticJsonPublisher(
            arguments.data_dir / "published", arguments.site_data_dir
        )
        outputs = publisher.publish()
        print(f"published {len(outputs)} validated JSON files")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
