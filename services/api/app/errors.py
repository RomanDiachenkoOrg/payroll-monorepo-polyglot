from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class ApiError(Exception):
    def __init__(self, status_code: int, message: str, field_errors: dict[str, str] | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.message = message
        self.field_errors = field_errors or {}


def not_found(what: str = "Resource") -> ApiError:
    return ApiError(404, f"{what} not found")


def conflict(message: str, field_errors: dict[str, str] | None = None) -> ApiError:
    return ApiError(409, message, field_errors)


def forbidden(message: str = "You do not have permission to do this") -> ApiError:
    return ApiError(403, message)


def bad_request(message: str, field_errors: dict[str, str] | None = None) -> ApiError:
    return ApiError(400, message, field_errors)


def _field_name(loc: tuple) -> str:
    parts = [str(p) for p in loc if p not in ("body", "query", "path")]
    return ".".join(parts) or "_"


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def handle_api_error(_: Request, exc: ApiError):
        return JSONResponse(status_code=exc.status_code, content={"message": exc.message, "fieldErrors": exc.field_errors})

    @app.exception_handler(HTTPException)
    async def handle_http_error(_: Request, exc: HTTPException):
        return JSONResponse(status_code=exc.status_code, content={"message": str(exc.detail), "fieldErrors": {}}, headers=exc.headers)

    @app.exception_handler(RequestValidationError)
    async def handle_validation(_: Request, exc: RequestValidationError):
        errors: dict[str, str] = {}
        for err in exc.errors():
            key = _field_name(tuple(err.get("loc", ())))
            msg = str(err.get("msg", "Invalid value"))
            if msg.startswith("Value error, "):
                msg = msg[len("Value error, ") :]
            errors.setdefault(key, msg)
        return JSONResponse(status_code=422, content={"message": "Please correct the highlighted fields", "fieldErrors": errors})
