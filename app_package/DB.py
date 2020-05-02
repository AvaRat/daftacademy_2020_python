from typing import List, Optional
import aiosqlite
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from fastapi.logger import logger


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

class Album_in(BaseModel):
    title: str
    artist_id: int


app = FastAPI()


@app.on_event("startup")
async def startup():
    app.db_connection = await aiosqlite.connect('chinook.db')
    app.db_connection.row_factory = aiosqlite.Row
    logger.info("Connection to database established")



@app.get("/tracks", response_model=List[Tracks])
async def get_tracks(page: int = 0, per_page: int = 10):
    cursor = await app.db_connection.execute("SELECT * FROM tracks ORDER BY TrackId LIMIT ? OFFSET ?;", (per_page, page*per_page))
    tracks = await cursor.fetchall()
    return tracks

@app.get("/tracks/composers", response_model = List[str])
async def get_tracks_composers(composer_name: str):
    cursor = await app.db_connection.execute("SELECT name FROM tracks WHERE composer== ? ORDER BY name ASC", [composer_name])
    tracks = await cursor.fetchall()
    if(len(tracks) > 0):
        return [track['name'] for track in tracks] 
    response = JSONResponse(content={'detail':{'error':'Composer not found'}}, status_code=status.HTTP_404_NOT_FOUND)
    return response
    
@app.post("/albums", status_code=201)
async def add_new_album(album: Album_in):
    cursor = await app.db_connection.execute("SELECT * FROM artists WHERE ArtistId==?", [album.artist_id])
    artists = await cursor.fetchall()
    if(len(artists) == 0):
        response = JSONResponse(content={'detail':{'error':'Artist with given ID not found'}}, status_code=status.HTTP_404_NOT_FOUND)
        return response
    cursor = await app.db_connection.execute("INSERT INTO albums (Title, ArtistId) VALUES (?, ?)", (album.title, album.artist_id))
    await app.db_connection.commit()
    added_id = cursor.lastrowid
    logger.error(added_id)
    cursor = await app.db_connection.execute("SELECT * FROM albums WHERE AlbumId==?", [added_id])
    album = await cursor.fetchone()
    return album


@app.on_event("shutdown")
async def shutdown():
    await app.db_connection.close()
    logger.info("Connection to database closed")
