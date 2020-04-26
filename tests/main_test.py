from fastapi.testclient import TestClient

from app_package.main import app

client = TestClient(app)


def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Witaj !!"}

def test_welcome():
    response = client.get("/welcome")
    assert response.status_code == 200
    assert response.json() == {"message":"Elo elo 320 w mojej pierwszej apce zdiplojowanej na Heroku!"}