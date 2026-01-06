from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
import boto3
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base

# ================= FASTAPI =================
app = FastAPI(title="FastAPI + Cognito Auth")

# ================= AWS COGNITO =================
AWS_REGION = "eu-north-1"
CLIENT_ID = "4n04p83m29pupn8ej4c57siv73"

cognito = boto3.client("cognito-idp", region_name=AWS_REGION)

# ================= DATABASE =================
DATABASE_URL = "mysql+pymysql://root:mohan%4028169@localhost/blogapplications"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# ================= USER MODEL =================
class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)          # Internal ID
    cognito_user_id = Column(String(255), index=True)           # Cognito UUID (sub)
    first_name = Column(String(100))
    last_name = Column(String(100))
    age = Column(Integer)
    email = Column(String(255), unique=True, index=True)

Base.metadata.create_all(bind=engine)

# ================= REQUEST SCHEMAS =================
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
# SIGNUP – CREATE USER + STORE COGNITO UUID
# ======================================================
@app.post("/signup")
def signup(request: SignupRequest):
    if request.password != request.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    try:
        response = cognito.sign_up(
            ClientId=CLIENT_ID,
            Username=request.email,
            Password=request.password,
            UserAttributes=[
                {"Name": "email", "Value": request.email},
                {"Name": "given_name", "Value": request.first_name},
                {"Name": "family_name", "Value": request.last_name}
            ]
        )

        cognito_user_id = response["UserSub"]

        db = SessionLocal()
        user = db.query(User).filter(User.email == request.email).first()

        if not user:
            user = User(
                cognito_user_id=cognito_user_id,
                first_name=request.first_name,
                last_name=request.last_name,
                age=request.age,
                email=request.email
            )
            db.add(user)
            db.commit()

        return {
            "message": "Signup successful. OTP sent to email.",
            "cognito_user_id": cognito_user_id
        }

    except cognito.exceptions.UsernameExistsException:
        raise HTTPException(status_code=400, detail="User already exists")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ======================================================
# VERIFY OTP
# ======================================================
@app.post("/verify-otp")
def verify_otp(request: OtpVerifyRequest):
    try:
        cognito.confirm_sign_up(
            ClientId=CLIENT_ID,
            Username=request.email,
            ConfirmationCode=request.otp
        )
        return {"message": "OTP verified successfully"}

    except cognito.exceptions.CodeMismatchException:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    except cognito.exceptions.ExpiredCodeException:
        raise HTTPException(status_code=400, detail="OTP expired")


# ======================================================
# LOGIN – SECURE (REQUEST BODY)
# ======================================================
@app.post("/login")
def login(request: LoginRequest):
    try:
        response = cognito.initiate_auth(
            ClientId=CLIENT_ID,
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={
                "USERNAME": request.email,
                "PASSWORD": request.password
            }
        )

        auth = response["AuthenticationResult"]

        return {
            "access_token": auth["AccessToken"],
            "id_token": auth["IdToken"],
            "refresh_token": auth["RefreshToken"]
        }

    except cognito.exceptions.NotAuthorizedException:
        raise HTTPException(status_code=401, detail="Invalid credentials")


# ======================================================
# GET USERS
# ======================================================
@app.get("/users")
def get_users():
    db = SessionLocal()
    users = db.query(User).all()

    return [
        {
            "id": u.id,
            "cognito_user_id": u.cognito_user_id,
            "first_name": u.first_name,
            "last_name": u.last_name,
            "age": u.age,
            "email": u.email
        }
        for u in users
    ]


# ======================================================
# UPDATE USER
# ======================================================
@app.put("/users/{user_id}")
def update_user(user_id: int, request: UpdateUserRequest):
    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()

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
# DELETE USER
# ======================================================
@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()

    return {"message": "User deleted successfully"}
