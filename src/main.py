from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi_jwt_auth.exceptions import AuthJWTException

from src.auth import auth_router
from src.database import db_startup, db_shutdown
from src.gov_structures import gov_structures_router
from src.users import users_router

app = FastAPI(
    title='event_manager'
)

app.include_router(users_router)
app.include_router(auth_router)
app.include_router(gov_structures_router)


@app.exception_handler(AuthJWTException)
def authjwt_exception_handler(request: Request, exc: AuthJWTException) -> JSONResponse:
    """The function that processes auth exceptions"""

    return JSONResponse(status_code=exc.status_code,
                        content=[{'loc': ['headers', 'token'],
                                  'msg': exc.message,
                                  'type': 'value_error'}])


@app.on_event('startup')
def startup() -> None:
    """The function that processes the start of the application"""

    db_startup()


@app.on_event('shutdown')
async def shutdown() -> None:
    """The function that processes the stop of the application"""

    await db_shutdown()
