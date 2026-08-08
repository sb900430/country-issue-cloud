from collections.abc import Callable
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.repositories.base import RepositoryDataError
from app.repositories.json_keyword_repository import JsonKeywordRepository
from app.schemas.issues import CountryCode
from app.schemas.keywords import CountryKeywordResult, KeywordResult

router = APIRouter()


def get_repository(request: Request) -> JsonKeywordRepository:
    return request.app.state.keyword_repository  # type: ignore[no-any-return]


RepositoryDependency = Annotated[JsonKeywordRepository, Depends(get_repository)]


def get_today_provider(request: Request) -> Callable[[], date]:
    return request.app.state.today_provider  # type: ignore[no-any-return]


TodayProviderDependency = Annotated[Callable[[], date], Depends(get_today_provider)]


def repository_failure() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail={"code": "keyword_repository_unavailable"},
    )


@router.get("/keywords/latest", response_model=KeywordResult)
def get_latest(repository: RepositoryDependency) -> KeywordResult:
    try:
        result = repository.find_latest()
    except RepositoryDataError as error:
        raise repository_failure() from error
    if result is None:
        raise HTTPException(status_code=404, detail={"code": "keyword_not_found"})
    return result


@router.get("/keywords/dates", response_model=list[date])
def get_dates(
    repository: RepositoryDependency,
    within_days: Annotated[int, Query(ge=1, le=7)] = 7,
) -> list[date]:
    try:
        return repository.find_available_dates(within_days)
    except RepositoryDataError as error:
        raise repository_failure() from error


@router.get("/keywords/{target_date}", response_model=KeywordResult)
def get_by_date(
    target_date: date,
    repository: RepositoryDependency,
    today_provider: TodayProviderDependency,
) -> KeywordResult:
    age = (today_provider() - target_date).days
    if age < 0 or age >= 7:
        raise HTTPException(status_code=400, detail={"code": "date_out_of_range"})
    try:
        result = repository.find_by_date(target_date)
    except RepositoryDataError as error:
        raise repository_failure() from error
    if result is None:
        raise HTTPException(status_code=404, detail={"code": "keyword_not_found"})
    return result


@router.get("/keywords/{target_date}/{country}", response_model=CountryKeywordResult)
def get_country(
    target_date: date,
    country: CountryCode,
    repository: RepositoryDependency,
    today_provider: TodayProviderDependency,
) -> CountryKeywordResult:
    result = get_by_date(target_date, repository, today_provider)
    return result.countries[country]
