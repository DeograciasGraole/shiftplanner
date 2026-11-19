from fastapi import FastAPI
from app.routers.v1 import auth, employee

import asyncio

from app.services.sms_service import send_activation_sms
# from fastapi.exceptions import RequestValidationError
# from starlette.exceptions import HTTPException as StarletteHTTPException
app = FastAPI()
app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
app.include_router(employee.router, prefix="/api/v1", tags=["employee"])




# # ── Global exception handlers ────────────────────────────
# @app.exception_handler(StarletteHTTPException)
# async def http_exception_handler(request, exc: StarletteHTTPException):
#     return JSONResponse(
#         status_code=exc.status_code,
#         content={"detail": exc.detail},
#     )


# @app.exception_handler(RequestValidationError)
# async def validation_exception_handler(request, exc: RequestValidationError):
#     errors = []
#     for error in exc.errors():
#         errors.append({
#             "field":   " → ".join(str(loc) for loc in error.get("loc", [])),
#             "message": error.get("msg", "Validation error"),
#         })
#     return JSONResponse(
#         status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
#         content={"detail": errors},
#     )
