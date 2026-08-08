from collections.abc import Callable
from datetime import date, datetime
from zoneinfo import ZoneInfo

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.v1.router import router
from app.api.v2.router import router as keyword_router
from app.core.settings import Settings, get_settings
from app.repositories import IssueRepository, JsonIssueRepository
from app.repositories.json_keyword_repository import JsonKeywordRepository


def create_app(
    settings: Settings | None = None,
    repository: IssueRepository | None = None,
    keyword_repository: JsonKeywordRepository | None = None,
    today_provider: Callable[[], date] | None = None,
) -> FastAPI:
    resolved_settings = settings or get_settings()
    app = FastAPI(title="Country Issue Cloud", version="0.1.0")

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        error: RequestValidationError,
    ) -> JSONResponse:
        del request
        fields = {str(item) for issue in error.errors() for item in issue.get("loc", ())}
        if "target_date" in fields:
            code = "invalid_date"
        elif "country" in fields:
            code = "invalid_country"
        else:
            code = "invalid_request"
        return JSONResponse(status_code=400, content={"detail": {"code": code}})

    app.state.issue_repository = repository or JsonIssueRepository(resolved_settings.data_dir)
    app.state.keyword_repository = keyword_repository or JsonKeywordRepository(
        resolved_settings.data_dir
    )
    app.state.today_provider = today_provider or (
        lambda: datetime.now(tz=ZoneInfo(resolved_settings.service_timezone)).date()
    )
    app.include_router(router, prefix=resolved_settings.api_prefix)
    app.include_router(keyword_router, prefix="/api/v2")
    return app


app = create_app()
