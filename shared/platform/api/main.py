from __future__ import annotations

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .routers import auth, dashboard, datalake, governance, me, platform, products
from .routers import observability
from .deps import error_response

app = FastAPI(
    title="Data Platform API",
    version="1.0.0",
    description="Platform operations API for Data Platform console.",
)

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(products.router)
app.include_router(datalake.router)
app.include_router(governance.router)
app.include_router(platform.router)
app.include_router(me.router)
app.include_router(observability.router)


def _error_code_for_status(status_code: int) -> str:
    if status_code == 400:
        return 'BAD_REQUEST'
    if status_code == 401:
        return 'UNAUTHORIZED'
    if status_code == 403:
        return 'FORBIDDEN'
    if status_code == 404:
        return 'NOT_FOUND'
    if status_code == 422:
        return 'VALIDATION_ERROR'
    return 'INTERNAL_ERROR'


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc: StarletteHTTPException):
    payload = error_response(
        request=request,
        code=_error_code_for_status(exc.status_code),
        message=str(exc.detail),
    )
    return JSONResponse(status_code=exc.status_code, content=payload)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    payload = error_response(
        request=request,
        code='VALIDATION_ERROR',
        message='Request validation failed',
        details={'errors': exc.errors()},
    )
    return JSONResponse(status_code=422, content=payload)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy"}
