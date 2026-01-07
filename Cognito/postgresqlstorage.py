from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
import boto3
import uuid
import requests
from jose import jwt

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    func
)
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.dialects.postgresql import UUID

# ======================================================
# FASTAPI (Swagger Tags)
# ======================================================
app = FastAPI(
    title="FastAPI + Cognito + PostgreSQL",
    openapi_tags=[
        {
            "name": "Cognito Auth",
            "description": "Signup, OTP verification and login using AWS Cognito",
        },
        {
            "name": "User Management",
            "description": "Protected user CRUD operations using Cognito Access Token",
        },
    ],
)

# ======================================================
# AWS COGNITO
# ======================================================
AWS_REGION = "eu-north-1"
CLIENT_ID = "4n04p83m29pupn8ej4c57siv73"
USER_POOL_ID = "eu-north-1_v7502wNHH"  # ✅ correct & required

cognito = boto3.client("cognito-idp", region_name=AWS_REGION)

# ======================================================
# TOKEN VALIDATION
# ======================================================
security = HTTPBearer()

COGNITO_ISSUER = f"https://cognito-idp.{AWS_REGION}.amazonaws.com/{USER_POOL_ID}"
JWKS_URL = f"{COGNITO_ISSUER}/.well-known/jwks.json"
jwks = requests.get(JWKS_URL).json()

def verify_access_token(
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    token = credentials.credentials
    try:
        header = jwt.get_unverified_header(token)
        key = next(k for k in jwks["keys"] if k["kid"] == header["kid"])

        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            issuer=COGNITO_ISSUER,
            options={"verify_aud": False},
        )
        return payload

    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired access token")

# ======================================================
# DATABASE
# ======================================================
DATABASE_URL = "postgresql+psycopg2://postgres:Mohan%4028169@localhost:5432/mydb"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# ======================================================
# USER MODEL
# ======================================================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    cognito_user_id = Column(UUID(as_uuid=True), unique=True, nullable=False)

    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    age = Column(Integer)
    email = Column(String(255), unique=True, index=True, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login_at = Column(DateTime(timezone=True))
    deleted_at = Column(DateTime(timezone=True))

Base.metadata.create_all(bind=engine)

# ======================================================
# SCHEMAS
# ======================================================
class SignupRequest(BaseModel):
    first_name: str
    last_name: str
    age: int
    email: EmailStr
    password: str
    confirm_password: str

class OtpVerifyRequest(BaseModel):
    email: EmailStr
    otp: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class UpdateUserRequest(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    age: int | None = None

# ======================================================
# SIGNUP
# ======================================================
@app.post("/signup", tags=["Cognito Auth"])
def signup(request: SignupRequest):
    if request.password != request.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    try:
        res = cognito.sign_up(
            ClientId=CLIENT_ID,
            Username=request.email,
            Password=request.password,
            UserAttributes=[
                {"Name": "email", "Value": request.email},
                {"Name": "given_name", "Value": request.first_name},
                {"Name": "family_name", "Value": request.last_name},
            ],
        )

    except cognito.exceptions.UsernameExistsException:
        raise HTTPException(
            status_code=400,
            detail="User already exists. Please verify OTP or login.",
        )

    except cognito.exceptions.InvalidPasswordException as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Cognito error: {str(e)}",
        )

    db = SessionLocal()
    db.add(User(
        cognito_user_id=uuid.UUID(res["UserSub"]),
        first_name=request.first_name,
        last_name=request.last_name,
        age=request.age,
        email=request.email,
    ))
    db.commit()

    return {"message": "Signup successful. OTP sent to email"}

# ======================================================
# VERIFY OTP
# ======================================================
@app.post("/verify-otp", tags=["Cognito Auth"])
def verify_otp(request: OtpVerifyRequest):
    cognito.confirm_sign_up(
        ClientId=CLIENT_ID,
        Username=request.email,
        ConfirmationCode=request.otp,
    )
    return {"message": "OTP verified successfully"}

# ======================================================
# LOGIN
# ======================================================
@app.post("/login", tags=["Cognito Auth"])
def login(request: LoginRequest):
    response = cognito.initiate_auth(
        ClientId=CLIENT_ID,
        AuthFlow="USER_PASSWORD_AUTH",
        AuthParameters={
            "USERNAME": request.email,
            "PASSWORD": request.password,
        },
    )

    db = SessionLocal()
    user = db.query(User).filter(
        User.email == request.email,
        User.deleted_at.is_(None)
    ).first()

    if user:
        user.last_login_at = func.now()
        db.commit()

    return response["AuthenticationResult"]

# ======================================================
# GET USERS (PROTECTED)
# ======================================================
@app.get("/users", tags=["User Management"])
def get_users(token=Depends(verify_access_token)):
    db = SessionLocal()
    return db.query(User).filter(User.deleted_at.is_(None)).all()

# ======================================================
# UPDATE USER (PROTECTED)
# ======================================================
@app.put("/users/{user_id}", tags=["User Management"])
def update_user(
    user_id: int,
    request: UpdateUserRequest,
    token=Depends(verify_access_token),
):
    db = SessionLocal()
    user = db.query(User).filter(
        User.id == user_id,
        User.deleted_at.is_(None)
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if request.first_name:
        user.first_name = request.first_name
    if request.last_name:
        user.last_name = request.last_name
    if request.age is not None:
        user.age = request.age

    db.commit()
    return {"message": "User updated successfully"}

# ======================================================
# DELETE USER (PROTECTED)
# ======================================================
@app.delete("/users/{user_id}", tags=["User Management"])
def delete_user(
    user_id: int,
    token=Depends(verify_access_token),
):
    db = SessionLocal()
    user = db.query(User).filter(
        User.id == user_id,
        User.deleted_at.is_(None)
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.deleted_at = func.now()
    db.commit()

    return {"message": "User deleted successfully"}
