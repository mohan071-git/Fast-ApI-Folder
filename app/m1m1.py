from fastapi import FastAPI, HTTPException, Depends, status
from typing import  Optional
from pydantic import BaseModel
from typing import Annotated
import app.models as models
from app.database import SessionaLocal
from sqlalchemy.orm import Session

app=FastAPI()

class PostBase(BaseModel):
    id:int
    content: Optional[str] = None
    user_id: Optional[int] = None
  
    


class UserBase(BaseModel):
    username:str


def get_db():
    db=SessionaLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency=Annotated[Session, Depends(get_db)]


@app.post('/posts/',status_code=status.HTTP_201_CREATED)
async def create_post(post:PostBase,db:db_dependency):
    db_post=models.Posts(**post.dict())
    db.add(db_post)
    db.commit()


@app.get('/posts/{post_id}', status_code=status.HTTP_200_OK)
async def read_post(post_id:int,db:db_dependency):
    post=db.query(models.Posts).filter(models.Posts.id==post_id).first()
    if post is None:
        HTTPException(status_code=404,details='post not found')
    return post



@app.put('/posts/{post_id}', status_code=status.HTTP_200_OK)
async def update_post(post_id: int, Post: PostBase, db: db_dependency):
    db_post = db.query(models.Posts).filter(models.Posts.id == post_id).first()
    if db_post is None:
        raise HTTPException(status_code=404, detail="Post was not found")
    db_post.content = Post.content
    db_post.user_id = Post.user_id
    db.commit()
    return {"message": "Post updated successfully"}



@app.delete("/posts/{post_id}",status_code=status.HTTP_200_OK)
async def delete_post(post_id:int,db:db_dependency):
    db_post=db.query(models.Posts).filter(models.Posts.id==post_id).first()
    if db_post is None:
        raise HTTPException(status_code=404,detail='Post was not found')
    db.delete(db_post)
    db.commit()


@app.post("/users/{user_id}",status_code=status.HTTP_201_CREATED)
async def create_user(user:UserBase,db:db_dependency):
    db_user=models.User(**user.dict())
    db.add(db_user)
    db.commit()


@app.get("/user/{user_id}",status_code=status.HTTP_200_OK)
async def read_user(user_id:int, db:db_dependency):
    user=db.query(models.User).filter(models.User.id==user_id)
    if user is None:
        raise HTTPException(Status_code=404,detail='user not found')
    return user
