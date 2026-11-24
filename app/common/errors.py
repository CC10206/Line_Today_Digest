class AppError(Exception):
    code: str = "INTERNAL_ERROR"
    message: str = "internal error"


class ArticleNotFound(AppError):
    code = "ARTICLE_NOT_FOUND"

    def __init__(self, article_id: int):
        self.message = f"article {article_id} not found"


# TODO: 註冊 FastAPI exception_handler，統一回傳 {"code": ..., "message": ...}
