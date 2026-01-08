from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
import boto3, uuid, requests
from jose import jwt

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    func,
    or_
)
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.dialects.postgresql import UUID


from botocore.exceptions import ClientError
from sqlalchemy.exc import IntegrityError
# ======================================================
# FASTAPI
# ======================================================

app = FastAPI(
    title="FastAPI + Cognito + PostgreSQL",
    openapi_tags=[
        {"name": "Cognito Auth"},
        {"name": "User Management"},
    ],
)

# ======================================================
# AWS COGNITO
# ======================================================
AWS_REGION = "eu-north-1"
CLIENT_ID = "4n04p83m29pupn8ej4c57siv73"
USER_POOL_ID = "eu-north-1_v7502wNHH"
cognito = boto3.client("cognito-idp", region_name=AWS_REGION)

# ======================================================
# TOKEN VALIDATION
# ======================================================
security = HTTPBearer()
ISSUER = f"https://cognito-idp.{AWS_REGION}.amazonaws.com/{USER_POOL_ID}"
jwks = requests.get(f"{ISSUER}/.well-known/jwks.json").json()

def verify_access_token(
    credentials: HTTPAuthorizationCredentials = Security(security),
):
    token = credentials.credentials
    header = jwt.get_unverified_header(token)
    key = next(k for k in jwks["keys"] if k["kid"] == header["kid"])

    return jwt.decode(
        token,
        key,
        algorithms=["RS256"],
        issuer=ISSUER,
        options={"verify_aud": False},
    )

# ======================================================
# DATABASE
# ======================================================
DATABASE_URL = "postgresql+psycopg2://postgres:Mohan%4028169@localhost:5432/mydb"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# ======================================================
# MODEL
# ======================================================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    cognito_user_id = Column(UUID(as_uuid=True), unique=True, nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    age = Column(Integer)
    email = Column(String(255), unique=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    last_login_at = Column(DateTime)
    deleted_at = Column(DateTime)

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

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class UpdateUserRequest(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    age: int | None = None

class OtpVerifyRequest(BaseModel):
    email: EmailStr
    otp: str
# ======================================================
# HELPER: FIND USER BY ANY IDENTIFIER
# ======================================================
def find_user(db, identifier: str):
    # ID or AGE
    if identifier.isdigit():
        return db.query(User).filter(
            or_(
                User.id == int(identifier),
                User.age == int(identifier)
            ),
            User.deleted_at.is_(None)
        ).first()

    # UUID
    try:
        return db.query(User).filter(
            User.cognito_user_id == uuid.UUID(identifier),
            User.deleted_at.is_(None)
        ).first()
    except ValueError:
        pass

    # EMAIL
    if "@" in identifier:
        return db.query(User).filter(
            User.email.ilike(identifier),
            User.deleted_at.is_(None)
        ).first()

    # NAME (partial match)
    return db.query(User).filter(
        or_(
            User.first_name.ilike(f"%{identifier}%"),
            User.last_name.ilike(f"%{identifier}%")
        ),
        User.deleted_at.is_(None)
    ).first()

# ======================================================
# SIGNUP
# ======================================================
from botocore.exceptions import ClientError
from sqlalchemy.exc import IntegrityError

@app.post("/signup", tags=["Cognito Auth"])
def signup(request: SignupRequest):
    if request.password != request.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    try:
        # --- Cognito signup ---
        res = cognito.sign_up(
            ClientId=CLIENT_ID,
            Username=request.email,
            Password=request.password,
            UserAttributes=[
                {"Name": "email", "Value": request.email},
            ],
        )

        # --- DB insert ---
        db = SessionLocal()
        user = User(
            cognito_user_id=uuid.UUID(res["UserSub"]),
            first_name=request.first_name,
            last_name=request.last_name,
            age=request.age,
            email=request.email,
        )
        db.add(user)
        db.commit()
        db.close()

        return {"message": "Signup successful. OTP sent to email"}

    except cognito.exceptions.UsernameExistsException:
        raise HTTPException(
            status_code=400,
            detail="User already exists. Please verify OTP or login.",
        )

    except IntegrityError:
        raise HTTPException(
            status_code=400,
            detail="User already exists in database",
        )

    except ClientError as e:
        raise HTTPException(
            status_code=400,
            detail=e.response["Error"]["Message"],
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )

# ======================================================
# VERIFY OTP (MANDATORY)
# ======================================================
@app.post("/verify-otp", tags=["Cognito Auth"])
def verify_otp(request: OtpVerifyRequest):
    try:
        cognito.confirm_sign_up(
            ClientId=CLIENT_ID,
            Username=request.email,
            ConfirmationCode=request.otp,
        )
        return {"message": "OTP verified successfully. You can login now."}

    except cognito.exceptions.CodeMismatchException:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    except cognito.exceptions.ExpiredCodeException:
        raise HTTPException(status_code=400, detail="OTP expired")

    except cognito.exceptions.UserNotFoundException:
        raise HTTPException(status_code=404, detail="User not found")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
# GET USER BY IDENTIFIER
# ======================================================
@app.get("/users", tags=["User Management"])
def get_logged_in_user(
    token_payload=Depends(verify_access_token),
):
    db = SessionLocal()

    # UUID from Cognito access token
    cognito_uuid = uuid.UUID(token_payload["sub"])

    user = db.query(User).filter(
        User.cognito_user_id == cognito_uuid,
        User.deleted_at.is_(None)
    ).first()

    db.close()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user



# ======================================================
# UPDATE USER BY IDENTIFIER
# ======================================================
@app.put("/users/search", tags=["User Management"])
def update_user(
    identifier: str,
    request: UpdateUserRequest,
    token=Depends(verify_access_token),
):
    db = SessionLocal()
    user = find_user(db, identifier)

    if not user:
        raise HTTPException(404, "User not found")

    if request.first_name:
        user.first_name = request.first_name
    if request.last_name:
        user.last_name = request.last_name
    if request.age is not None:
        user.age = request.age

    db.commit()

    return {
        "message": "User updated",
        "id": user.id,
        "uuid": str(user.cognito_user_id),
    }

# ======================================================
# DELETE USER BY IDENTIFIER (SOFT DELETE)
# ======================================================
@app.delete("/users/search", tags=["User Management"])
def delete_user(
    identifier: str,
    token=Depends(verify_access_token),
):
    db = SessionLocal()
    user = find_user(db, identifier)

    if not user:
        raise HTTPException(404, "User not found")

    user.deleted_at = func.now()
    db.commit()

    return {
        "message": "User deleted",
        "id": user.id,
        "uuid": str(user.cognito_user_id),
    }
