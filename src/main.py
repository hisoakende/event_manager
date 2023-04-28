from fastapi import FastAPI

from src.database import db_startup, db_shutdown

app = FastAPI(
    title='event_manager'
)


@app.on_event('startup')
def startup() -> None:
    db_startup()


@app.on_event('shutdown')
async def shutdown() -> None:
    await db_shutdown()
