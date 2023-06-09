from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi_jwt_auth.exceptions import AuthJWTException

import src.auth.router
import src.events.router
import src.gov_structures.router
import src.users.router
from src.database import db_start_up, db_shut_down

app = FastAPI(
    title='event_manager'
)

app.include_router(src.users.router.users_router)
app.include_router(src.auth.router.auth_router)
app.include_router(src.gov_structures.router.gov_structures_router)
app.include_router(src.events.router.events_router)


@app.exception_handler(AuthJWTException)
def authjwt_exception_handler(request: Request, exc: AuthJWTException) -> JSONResponse:
    """The function that processes auth exceptions"""

    return JSONResponse(status_code=exc.status_code,
                        content=[{'loc': ['headers', 'token'],
                                  'msg': exc.message,
                                  'type': 'value_error'}])


@app.on_event('startup')
async def start_up() -> None:
    """The function that processes the start of the application"""

    db_start_up()


@app.on_event('shutdown')
async def shut_down() -> None:
    """The function that processes the stop of the application"""

    await db_shut_down()
