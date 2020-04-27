import secrets

from starlette.responses import RedirectResponse, Response
from fastapi import Depends, FastAPI, HTTPException, status, Response, Cookie
from fastapi.security import HTTPBasic, HTTPBasicCredentials

class SessionManager:
    def __init__(self):
        self.data_base = {}
    
    def new_session(self, username):
        from datetime import datetime

        now = datetime.now()
        current_time = now.strftime("%m/%d/%Y, %H:%M:%S")
        self.data_base[hash(username)] = current_time
    
    def get_session_time(self, username):
        return self.data_base[hash(username)]

DB = {} #normal dict for now is fine
app = FastAPI()
session_manager = SessionManager()

DB['session_manager']=session_manager
DB['users_data']=[{'username':'trudnY', 'password':'PaC13Nt'}]

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

@app.get("/")
async def main_page():
    response = RedirectResponse(url='/login')
    return response

@app.get("/login")
def read_current_user(credentials: str = Depends(get_current_username)):
    response = RedirectResponse(url='/welcome')
    user = credentials.username
    session_manager.new_session(user)
    response.set_cookie('username', user, max_age=40)
    #response.set_cookie('passwd_hash', hash(credentials.password), max_age=40)
    return response

@app.get("/welcome/")
async def read_items(*, username: str = Cookie(None)):
    return {"init time": session_manager.get_session_time(username), "current user": username}

#@app.post("/cookie-and-object/")
#def create_cookie(response: Response):
#    response.set_cookie(key="fakesession", value="fake-cookie-session-value")
#    return {"message": "Come to the dark side, we have cookies"}

#@app.get('/get_cookie')
#async def get_cookie():
#    response = Response('you received a cookie', status_code=200, headers=None, media_type=None)
#    response.set_cookie('username','Marcel1928')
#    return response

