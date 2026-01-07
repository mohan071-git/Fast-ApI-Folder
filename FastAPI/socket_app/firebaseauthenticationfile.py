#model of firebase authentication
from pydantic import BaseModel, EmailStr

class SignUpSchema(BaseModel):
    email: EmailStr
    password: str

class LoginSchema(BaseModel):
    email: EmailStr
    password: str
  
#database of firebase authentication
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

URL_DATABASE = "mysql+pymysql://root:mohan%4028169@localhost:3306/blogapplications"

engine = create_engine(URL_DATABASE)

SessionaLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()
#serviceAccountkey.json file of firebase authentication
#{
  #"type": "service_account",
  #"project_id": "fastapiauth-3badb",
  #"private_key_id": "2bbccf8ba51556fab03cde8192b4139d09794c8f",
  #"private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQCq4CuanN6/ffAe\nUrZfafIFCYHvyTxPf+/rUB2hnxowQGKvXv+s7BGAp2QMZLS7G9qh7wG4LvIa4GmD\n7qYOPugCHSF40Y5nceFGP4cmgZPAK97nEq1fGSmgTisyMowuuapR8CPyfMMbaPCy\ni/AaZxahjQNYnPAEpdyXPKQvrEw+t+Aq1WA/urHSPE5v+594ZDROEmaZBR142mDR\nYFjs5RLZ/60Id56mWxtsvQXdeLFsv0P289FP9Uo+uktyyXiYon+Vuwir3ABSW11O\nWwq5SQ/mnr0WSibnxrAngxtVNXjuSpRXOSpuufveviR+cXwY1bVclNrKS9o5WOMA\nrWBZ0mK3AgMBAAECggEAKkgS8gyb/4Uxm8c6skxcYwuxt7wzLLbLDo6B7oKYb9UW\nti9LE6ZMRGnnEzv+Doh7ZnNmGQWgya663Tb5pu/A5/j+Vc+Ara8bn47LqecJQNV6\nL/JKrQvkZXLCNIcWcd9mOiUyN+fQPWGPoZaH4HievHXQnKYkq/nApjmOpO885I2i\nBbU4bDtfUZsxRcB8/+A6sUV+70tSewFDZGhhzJA6/FgvasGDkHUAFOTj3kmcHhWS\nSK2/7q2WSjxTKBZ1zg+U0Vx7mZe1iqV36GWDR/Gy3JPITVTuXJ3AERT8rJCEdlty\ns4oE5jx2lPXro7cZ+UzBLndV1btDowHa3ELRSRLGAQKBgQDp8+afbS1lyP7kX88H\nYPhZxkYPfJpykx0N29jzgzg8G9MIjUxHmpRj8qFqo3ms5fYrp2qecfNuucKV0vjW\n9hisS8P3b8l1VQxoTr1oZhVCq1wzvqpezffdevCmzVUcvCumCjnu0afjNjfcv+UT\nU84RmXRL7ymVowngML6IDp3SAQKBgQC6+om331GHaLc/aMNnyYseFJYONnfSOVsw\niL+ZrrFaXFfqsSjrbj4p8BiEFrrOYk7e9GybmGOTZOlae6F2nd4OOG34lUC1Ro6f\naCWHRpTaAZcG8+njRr352caL1qvQkTAY/smpqA1jD43rVig71dKtOQD/DH8P+Ya3\nIWVWOTlEtwKBgQDi9aQz4Zx69ASi1Hdpdx83KGxrNbw3jpRPD4pmolP5rByMXVc0\n17dBRu5lH3Y4z1aDfwSl9XHtZvRomKSjFVdWPqI79wx/cSR6RHjnQLE7XjYyVLO/\nCR1+lXfEucnp+Hp3t8//6RBwEfcbhmXa3CA7Xp091SSIcARyo5cTMurUAQKBgAIr\n0JeS/0ZcP+x7kfFNlND3mjp2BXQqeFWa8Oae8a5D7j1qazg4on4oLJC0Ft04pQPP\nwMcZwOZAQLltQBW5hY+Stiwxx3uTYyqUsgLdHfNeG1vYTzn1Y1VYYwbSqlIUrYNM\nyhivO+CPmK1H5dW0COs8Azfy9DLCSf8sYxnaNkEHAoGBAMaoZrWlzYu6+pcZTf6E\nGZG+H6K8lsCeV9fZI81qbxXYOIYcTDOgmyYdkYww01WljXsvHFH4jTVxQqq2oVEt\nYr//GeUHhpqHWQEs/co4ArnZU/4Xi9j9N/eDkocU8tTCMxE+JvpN2f/1a01vTmE8\nP6RC3X0rkvZ2pBJwCPY8m46L\n-----END PRIVATE KEY-----\n",
  #"client_email": "firebase-adminsdk-fbsvc@fastapiauth-3badb.iam.gserviceaccount.com",
  #"client_id": "100454984315490192597",
  #"auth_uri": "https://accounts.google.com/o/oauth2/auth",
  #"token_uri": "https://oauth2.googleapis.com/token",
  #"auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  #"client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40fastapiauth-3badb.iam.gserviceaccount.com",
  #"universe_domain": "googleapis.com"
}

#main method of firebase authentication
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Annotated
import requests

import pep.models as models
from pep.database import SessionaLocal
from firebase.firebase import verify_firebase_token

# -------------------- APP --------------------

app = FastAPI(title="FastAPI + Firebase Auth")

# -------------------- FIREBASE API KEY --------------------
# (Hard-coded as you requested)

FIREBASE_API_KEY = "AIzaSyCC6S5ApQxOmnN89i_rb_S5AcgroEAQoQ0"

# -------------------- DATABASE DEPENDENCY --------------------

def get_db():
    db = SessionaLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

# -------------------- FIREBASE AUTH --------------------

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials
    user = verify_firebase_token(token)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Firebase token"
        )

    return user

# -------------------- SCHEMAS --------------------

class PostBase(BaseModel):
    id: Optional[int] = None
    content: Optional[str] = None
    user_id: Optional[int] = None

class LoginSchema(BaseModel):
    email: str
    password: str

# -------------------- FIREBASE LOGIN --------------------

@app.post("/login", summary="Login using Firebase")
def firebase_login(
    data: LoginSchema,
    db: Session = Depends(get_db)
):
    url = (
        "https://identitytoolkit.googleapis.com/v1/"
        f"accounts:signInWithPassword?key={FIREBASE_API_KEY}"
    )

    payload = {
        "email": data.email,
        "password": data.password,
        "returnSecureToken": True
    }

    response = requests.post(url, json=payload)
    result = response.json()

    # DEBUG (keep for now)
    print("FIREBASE RESPONSE:", result)

    if "idToken" not in result:
        log_post = models.Posts(
            content=f"LOGIN FAILED | email={data.email}",
            user_id=None
        )
        db.add(log_post)
        db.commit()
        raise HTTPException(status_code=401, detail="Invalid credentials")

    log_post = models.Posts(
        content=f"LOGIN SUCCESS | email={data.email}",
        user_id=None
    )
    db.add(log_post)
    db.commit()

    return {
        "access_token": result["idToken"],
        "token_type": "Bearer",
        "expires_in": int(result["expiresIn"])
    }

# -------------------- POSTS APIs (PROTECTED) --------------------

@app.post("/posts/", status_code=status.HTTP_201_CREATED)
async def create_post(
    post: PostBase,
    db: db_dependency,
    user: dict = Depends(get_current_user)
):
    db_post = models.Posts(
        content=post.content,
        user_id=post.user_id
    )
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post


@app.get("/posts/{post_id}", status_code=status.HTTP_200_OK)
async def read_post(
    post_id: int,
    db: db_dependency,
    user: dict = Depends(get_current_user)
):
    post = db.query(models.Posts).filter(models.Posts.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@app.put("/posts/{post_id}", status_code=status.HTTP_200_OK)
async def update_post(
    post_id: int,
    post: PostBase,
    db: db_dependency,
    user: dict = Depends(get_current_user)
):
    db_post = db.query(models.Posts).filter(models.Posts.id == post_id).first()
    if not db_post:
        raise HTTPException(status_code=404, detail="Post not found")

    db_post.content = post.content
    db_post.user_id = post.user_id
    db.commit()

    return {"message": "Post updated successfully"}


@app.delete("/posts/{post_id}", status_code=status.HTTP_200_OK)
async def delete_post(
    post_id: int,
    db: db_dependency,
    user: dict = Depends(get_current_user)
):
    db_post = db.query(models.Posts).filter(models.Posts.id == post_id).first()
    if not db_post:
        raise HTTPException(status_code=404, detail="Post not found")

    db.delete(db_post)
    db.commit()

    return {"message": "Post deleted successfully"}
