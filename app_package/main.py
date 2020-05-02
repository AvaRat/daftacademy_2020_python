import secrets

from fastapi import Depends, FastAPI, HTTPException, status, Response, Cookie
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel

class UserCredentials(BaseModel):
    username: str
    password: str

class SessionManager:
    def __init__(self):
        self.data_base = {}
    
    def new_session(self, username):
        from datetime import datetime

        now = datetime.now()
        current_time = now.strftime("%m/%d/%Y, %H:%M:%S")
        self.data_base[username] = current_time
    
    def get_session_time(self, username):
        return self.data_base[username]
    
    def quit_session(self, username):
        del self.data_base[username]

DB = {} #normal dict for now is fine
app = FastAPI()
session_manager = SessionManager()

DB['session_manager']=session_manager

security = HTTPBasic()



def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, "trudnY")
    correct_password = secrets.compare_digest(credentials.password, "PaC13Nt")
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials



async def verify_cookie(session_id: str = Cookie(None)):
    if session_id==None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="session not initialized, you need to log in",
        )
    return session_id

@app.post("/logout")
async def logout(session_id: str = Depends(verify_cookie)):
    session_manager.quit_session(session_id)
    response = RedirectResponse(url='/', status_code=301)
    response.delete_cookie(key="session_id")
    return response

@app.get("/")
async def main_page():
    return {"message":"elo "}

@app.get("/patient")
async def patient(session_id: str = Depends(verify_cookie)):
    return {"message": "siema "+session_id}

@app.post("/login")
async def login(credentials: get_current_username = Depends()):
    user = credentials.username
    session_manager.new_session(user)
    response = RedirectResponse(url='/welcome', status_code=301)
    response.set_cookie(key="session_id", value=user, max_age=120)
    return response
    


@app.get("/welcome")
async def welcome_screen(session_id: str = Depends(verify_cookie)):
    return {"init time": session_manager.get_session_time(session_id), "current user": session_id}
