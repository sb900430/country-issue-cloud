from collections.abc import Callable
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.repositories import IssueRepository, RepositoryDataError
from app.schemas.issues import CountryCode, CountryIssueResult, IssueResult

router = APIRouter()


def get_repository(request: Request) -> IssueRepository:
    return request.app.state.issue_repository  # type: ignore[no-any-return]


RepositoryDependency = Annotated[IssueRepository, Depends(get_repository)]


def get_today_provider(request: Request) -> Callable[[], date]:
    return request.app.state.today_provider  # type: ignore[no-any-return]


TodayProviderDependency = Annotated[Callable[[], date], Depends(get_today_provider)]


def repository_failure() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail={"code": "repository_unavailable"},
    )


@router.get("/issues/latest", response_model=IssueResult)
def get_latest(repository: RepositoryDependency) -> IssueResult:
    try:
        result = repository.find_latest()
    except RepositoryDataError as error:
        raise repository_failure() from error
    if result is None:
        raise HTTPException(status_code=404, detail={"code": "issue_not_found"})
    return result


@router.get("/issues/dates", response_model=list[date])
def get_dates(
    repository: RepositoryDependency,
    within_days: Annotated[int, Query(ge=1, le=7)] = 7,
) -> list[date]:
    try:
        return repository.find_available_dates(within_days)
    except RepositoryDataError as error:
        raise repository_failure() from error


@router.get("/issues/{target_date}", response_model=IssueResult)
def get_by_date(
    target_date: date,
    repository: RepositoryDependency,
    today_provider: TodayProviderDependency,
) -> IssueResult:
    return find_by_date(target_date, repository, today_provider())


def find_by_date(
    target_date: date,
    repository: IssueRepository,
    today: date,
) -> IssueResult:
    age_in_days = (today - target_date).days
    if age_in_days < 0 or age_in_days >= 7:
        raise HTTPException(status_code=400, detail={"code": "date_out_of_range"})
    try:
        result = repository.find_by_date(target_date)
    except RepositoryDataError as error:
        raise repository_failure() from error
    if result is None:
        raise HTTPException(status_code=404, detail={"code": "issue_not_found"})
    return result


@router.get("/issues/{target_date}/{country}", response_model=CountryIssueResult)
def get_country(
    target_date: date,
    country: CountryCode,
    repository: RepositoryDependency,
    today_provider: TodayProviderDependency,
) -> CountryIssueResult:
    result = find_by_date(target_date, repository, today_provider())
    country_result = result.countries.get(country)
    if country_result is None:
        raise HTTPException(status_code=404, detail={"code": "country_not_available"})
    return country_result


@router.get("/status")
def get_status(repository: RepositoryDependency) -> dict[str, object]:
    try:
        result = repository.find_latest()
    except RepositoryDataError as error:
        raise repository_failure() from error
    if result is None:
        return {"status": "unavailable", "latest_date": None, "countries": {}}
    return {
        "status": result.status,
        "latest_date": result.date,
        "countries": {country: value.status for country, value in result.countries.items()},
    }


@router.get("/app-config")
def get_app_config() -> dict[str, object]:
    return {
        "maintenance": False,
        "schema_version": "1.0",
        "notice": None,
        "policy_urls": {},
    }


@router.get("/health")
def get_health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
def get_ready(repository: RepositoryDependency) -> dict[str, str]:
    try:
        repository.find_available_dates(within_days=1)
    except RepositoryDataError as error:
        raise repository_failure() from error
    return {"status": "ready"}
