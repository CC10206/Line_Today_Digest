from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    code: str = "INTERNAL_ERROR"
    message: str = "internal error"
    status_code: int = 500


class ArticleNotFound(AppError):
    code = "ARTICLE_NOT_FOUND"
    status_code = 404

    def __init__(self, article_id: int):
        self.message = f"article {article_id} not found"


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": exc.code, "message": exc.message},
        )
