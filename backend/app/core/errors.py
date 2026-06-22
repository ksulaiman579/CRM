from fastapi import status

class AppError(Exception):
    def __init__(
        self, 
        code: str, 
        message: str, 
        http_status: int = status.HTTP_400_BAD_REQUEST, 
        detail: str | None = None
    ):
        self.code = code
        self.message = message
        self.http_status = http_status
        self.detail = detail
        super().__init__(self.message)
