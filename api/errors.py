from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from libraryhub.errors import (
    InvalidISBNError,
    ItemNotFoundError,
    LibraryError,
    LoanNotFoundError,
    MemberNotFoundError,
    ValidationError,
)

# ValidationError fields that mean "state conflict", not "bad input"
CONFLICT_FIELDS = {"waiting_list", "isbn"}
import logging

logger = logging.getLogger(__name__)

def status_for(exc: LibraryError) -> int:
    if isinstance(exc, (ItemNotFoundError, MemberNotFoundError, LoanNotFoundError)):
        return 404
    if isinstance(exc, InvalidISBNError):
        return 422
    if isinstance(exc, ValidationError):
        return 409 if exc.field in CONFLICT_FIELDS else 422
    return 409  # R1 R2 R3 R4 R6 R7 R8, LoanAlreadyReturnedError


def body(code: str, message: str) -> dict:
    return {"error": code, "message": message}


def register_error_handlers(app) -> None:
    @app.exception_handler(LibraryError)
    async def library_error(request: Request, exc: LibraryError):
        return JSONResponse(status_code=status_for(exc), content=body(exc.code, exc.message))

    @app.exception_handler(RequestValidationError)
    async def bad_request(request: Request, exc: RequestValidationError):
        first = exc.errors()[0]
        field = ".".join(str(p) for p in first["loc"] if p != "body")
        return JSONResponse(status_code=422, content=body("ValidationError", f"{field}: {first['msg']}"))

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, exc: StarletteHTTPException):
        return JSONResponse(status_code=exc.status_code, content=body("HTTPError", str(exc.detail)))

    @app.exception_handler(Exception)
    async def unexpected(request: Request, exc: Exception):
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(status_code=500, content=body("ServerError", "Something went wrong. Please try again."))