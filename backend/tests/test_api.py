from datetime import date
from pathlib import Path
from shutil import copyfile

from fastapi.testclient import TestClient

from app.main import create_app
from app.repositories import JsonIssueRepository

SAMPLE_FIXTURE = Path(__file__).parents[2] / "sample-data" / "fixtures" / "issues_2026-08-03.json"


def test_issue_endpoints_return_published_data(tmp_path: Path) -> None:
    published_dir = tmp_path / "published"
    published_dir.mkdir()
    copyfile(SAMPLE_FIXTURE, published_dir / "issues_2026-08-03.json")
    copyfile(SAMPLE_FIXTURE, published_dir / "latest.json")
    client = TestClient(
        create_app(
            repository=JsonIssueRepository(
                tmp_path,
                today_provider=lambda: date(2026, 8, 4),
            ),
            today_provider=lambda: date(2026, 8, 4),
        )
    )

    latest = client.get("/api/v1/issues/latest")
    dates = client.get("/api/v1/issues/dates")
    country = client.get("/api/v1/issues/2026-08-03/JP")

    assert latest.status_code == 200
    assert latest.json()["date"] == "2026-08-03"
    assert dates.json() == ["2026-08-03"]
    assert country.status_code == 200
    assert country.json()["status"] == "success"


def test_issue_endpoint_returns_not_found_for_missing_date(tmp_path: Path) -> None:
    client = TestClient(
        create_app(
            repository=JsonIssueRepository(tmp_path),
            today_provider=lambda: date(2026, 8, 4),
        )
    )

    response = client.get("/api/v1/issues/2026-08-03")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "issue_not_found"


def test_invalid_date_and_country_are_rejected(tmp_path: Path) -> None:
    client = TestClient(
        create_app(
            repository=JsonIssueRepository(tmp_path),
            today_provider=lambda: date(2026, 8, 4),
        )
    )

    invalid_date = client.get("/api/v1/issues/not-a-date")
    invalid_country = client.get("/api/v1/issues/2026-08-03/GB")

    assert invalid_date.status_code == 400
    assert invalid_date.json()["detail"]["code"] == "invalid_date"
    assert invalid_country.status_code == 400
    assert invalid_country.json()["detail"]["code"] == "invalid_country"


def test_date_outside_recent_seven_days_is_rejected(tmp_path: Path) -> None:
    client = TestClient(
        create_app(
            repository=JsonIssueRepository(tmp_path),
            today_provider=lambda: date(2026, 8, 4),
        )
    )

    response = client.get("/api/v1/issues/2026-07-28")

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "date_out_of_range"


def test_health_ready_status_and_config_endpoints(tmp_path: Path) -> None:
    client = TestClient(create_app(repository=JsonIssueRepository(tmp_path)))

    assert client.get("/api/v1/health").json() == {"status": "ok"}
    assert client.get("/api/v1/ready").json() == {"status": "ready"}
    assert client.get("/api/v1/status").json()["status"] == "unavailable"
    assert client.get("/api/v1/app-config").json()["maintenance"] is False
