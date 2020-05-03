from typing import List, Optional, Union
import aiosqlite
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi.logger import logger
from pydantic import BaseModel, validator


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

class AlbumIn(BaseModel):
    title: str
    artist_id: int

    
class CustomerIn(BaseModel):
    company: str = None
    address: str = None
    city: str = None
    state: str = None
    country: str = None
    postalcode: str = None
    fax: str = None

def to_lower(string: str) -> str:
    return string.lower()

class CustomerDB(BaseModel):
    CustomerId: int
    FirstName: str
    LastName: str
    Company: str = None
    Address: str = None
    City: str = None
    State: str = None
    Country: str = None
    PostalCode: str = None
    Phone: str = None
    Fax: str = None
    Email: str
    SupportRepId: int = None
    class Config:
        alias_generator = to_lower
        allow_population_by_alias = False

class Customer_DB(BaseModel):
    CustomerId: int
    FirstName: str
    LastName: str
    Company: str = None
    Address: str = None
    City: str = None
    State: str = None
    Country: str = None
    PostalCode: str = None
    Phone: str = None
    Fax: str = None
    Email: str
    SupportRepId: int = None

class SalesSimple(BaseModel):
    CustomerId: int
    Email: str
    Phone: str = None
    Sum: float

    @validator("Sum")
    def round_up_sum(cls, Sum):
        return round(Sum, 2)
class SalesGenre(BaseModel):
    Name: str
    Sum: int


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
async def add_new_album(album: AlbumIn):
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

@app.get("/albums/{album_id}")
async def get_album_by_id(album_id: int):
    cursor = await app.db_connection.execute("SELECT * FROM albums WHERE AlbumId==?", [album_id])
    album = await cursor.fetchone()
    return album


@app.put("/customers/{customer_id}", response_model=Customer_DB)
async def add_customer(customer_id: int, customer_update: CustomerIn):
    cursor = await app.db_connection.execute("SELECT * FROM customers WHERE CustomerId==?", [customer_id])
    customer = await cursor.fetchall()
    if(len(customer) == 0):
        response = JSONResponse(content={'detail':{'error':'Resource not found'}}, status_code=status.HTTP_404_NOT_FOUND)
        return response

    customer_db = CustomerDB(**{k.lower():v for k,v in jsonable_encoder(customer[0]).items()})
    customer_dict = customer_db.dict(by_alias=True)

    for key in customer_update.__fields_set__:
         customer_dict[key] = customer_update.dict()[key]
    
    await app.db_connection.execute("UPDATE customers \
        SET company=?,  address=?, city=?, state=?, country=?, postalcode=?, fax=? \
        WHERE CustomerId==?", (customer_dict['company'], customer_dict['address'], customer_dict['city'], customer_dict['state'], 
            customer_dict['country'], customer_dict['postalcode'], customer_dict['fax'], customer_id))  
    await app.db_connection.commit()
    customer_out = CustomerDB(**customer_dict)
    logger.warn(customer_out.dict())

    return JSONResponse(content=jsonable_encoder(customer_out, by_alias=False))


@app.get("/sales", response_model=Union[List[SalesSimple], List[SalesGenre]])
async def get_sales_stats(category: str):
    if(category == 'customers'):
        cursor = await app.db_connection.execute("SELECT C.CustomerId, C.Email, C.Phone, SUM(I.Total) AS Sum \
                                                    FROM customers C INNER JOIN invoices I ON C.CustomerId=I.CustomerId \
                                                    GROUP BY C.CustomerId ORDER BY ROUND(SUM(I.Total)) DESC, C.CustomerId ")
        sales_list = await cursor.fetchall()
        return sales_list
    elif(category == 'genres'):
        cursor = await app.db_connection.execute("SELECT G.Name, SUM(I_I.Quantity) AS Sum, SUM(I.Total) AS TotalInvoiced \
                                                    FROM invoices I \
                                                    JOIN invoice_items I_I ON I_I.InvoiceId=I.InvoiceId \
                                                    JOIN tracks T ON T.TrackId=I_I.TrackId \
                                                    JOIN genres G ON G.GenreId=T.GenreId \
                                                    GROUP BY G.GenreId  \
                                                    ORDER BY SUM(I_I.Quantity) DESC, G.Name")
        sales_list = await cursor.fetchall()
        return sales_list

    response = JSONResponse(content={'detail':{'error':'Resource not found'}}, status_code=status.HTTP_404_NOT_FOUND)
    return response

@app.get("/compare")
async def compare():
    cursor = await app.db_connection.execute("SELECT C.CustomerId, C.Email, C.Phone, SUM(I.Total) AS Sum \
                                                FROM customers C  JOIN invoices I ON C.CustomerId=I.CustomerId \
                                                GROUP BY C.CustomerId ORDER BY SUM(I.Total) DESC, C.CustomerId ")
    sales_list = await cursor.fetchall()

    cursor = await app.db_connection.execute("SELECT CustomerId, Email, Phone, SUM(Total) AS Sum \
                                                FROM( \
	                                            SELECT * FROM invoices  \
	                                            JOIN customers ON customers.CustomerId = invoices.CustomerId \
                                                )GROUP BY CustomerId  \
                                                ORDER BY Sum DESC, CustomerId")
    sales_list_2 = await cursor.fetchall()
    s1 = set(sales_list)
    s2 = set(sales_list_2)

    for a1,a2 in zip(sales_list, sales_list_2):
        for k1,k2 in zip(a1.keys(), a2.keys()):
            if(a1[k1] != a2[k2]):
                logger.error('DIFFERENT')

    logger.info("THE SAME")


@app.on_event("shutdown")
async def shutdown():
    await app.db_connection.close()
    logger.info("Connection to database closed")
