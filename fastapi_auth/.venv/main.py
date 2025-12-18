from typing import Annotated
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Fake user data
fake_user = {
    "username": "admin",
    "password": "admin123",
    "token": "secrettoken"
}

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if (
        form_data.username != fake_user["username"]
        or form_data.password != fake_user["password"]
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    return {"access_token": fake_user["token"], "token_type": "bearer"}

@app.get("/items/")
async def read_items(token: Annotated[str, Depends(oauth2_scheme)]):
    if token != fake_user["token"]:
        raise HTTPException(status_code=401, detail="Invalid token")
    return {"message": "You are authenticated"}
