from fastapi import FastAPI, Depends, HTTPException, status
import models
from database import engine,SessionLocal
from typing import Annotated
from sqlaclhemy.orm import Session
from app.logger import logger
import auth
from auth import get_current_user

app=FastAPI()
app.include_router(auth.router)

def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()

dp_dependency=Annotated[Session,Depends(get_db)]
user_dependency=Annotated[dict,depends(get_current_user)]

@app.get("/",status_code=status.HTTP_200_OK)
async def user(user:user_dependency, db:db_dependency):

   if user is None:
       raise HTTPException(status_code=401,detail='Authentication Failed')
   return {"User":user}
