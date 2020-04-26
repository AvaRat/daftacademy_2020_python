from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Witaj !!"}

@app.get("/welcome")
def welcome():
    return {"message":"Elo elo 320 w mojej pierwszej apce zdiplojowanej na Heroku!"}

