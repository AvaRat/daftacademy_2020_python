from typing import List, Optional
import aiosqlite
import sqlite3
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.logger import logger

from databases import Database


# SQLAlchemy specific code, as with any other app
#DATABASE_URL = "sqlite:///./chinook.db"

class Tracks(BaseModel):
    TrackId: int
    Name: str
    AlbumId: Optional[int]
    MediaTypeId: int
    GenreId: Optional[int]
    Composer: Optional[str]
    Milliseconds: int
    Bytes: Optional[int]
    UnitPrice: float

app = FastAPI()


@app.on_event("startup")
async def startup():
    app.db_connection = await aiosqlite.connect('chinook.db')
    logger.info("Connection to database established")



@app.get("/tracks", response_model=List[Tracks])
async def get_tracks(page: int = 0, per_page: int = 10):
    app.db_connection.row_factory = sqlite3.Row
    cursor = await app.db_connection.execute("SELECT * FROM tracks ORDER BY TrackId LIMIT ? OFFSET ?;", (per_page, page))
    tracks = await cursor.fetchall()

    def make_dict(row):
        dict_row = {}
        for key in row.keys():
            dict_row[key] = row[key]
        return dict_row

    ret = [make_dict(row) for row in tracks]
    return ret

@app.on_event("shutdown")
async def shutdown():
    await app.db_connection.close()
    logger.info("Connection to database closed")

