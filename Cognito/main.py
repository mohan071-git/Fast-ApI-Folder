from fastapi import FastAPI, HTTPException
import boto3
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base

# ================= FASTAPI =================
app = FastAPI()

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

    id = Column(Integer, primary_key=True, index=True)
    cognito_user_id = Column(String(255), index=True)   # 🔑 Cognito UUID
    first_name = Column(String(100))
    last_name = Column(String(100))
    age = Column(Integer)
    email = Column(String(255), unique=True, index=True)
    password = Column(String(255))

Base.metadata.create_all(bind=engine)

# ======================================================
# SIGNUP – CREATE USER + STORE COGNITO UUID IN DB
# ======================================================
@app.post("/signup")
def signup(
    first_name: str,
    last_name: str,
    age: int,
    email: str,
    password: str,
    confirm_password: str
):
    if password != confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    try:
        # 1️⃣ Signup in Cognito
        response = cognito.sign_up(
            ClientId=CLIENT_ID,
            Username=email,
            Password=password,
            UserAttributes=[
                {"Name": "email", "Value": email},
                {"Name": "given_name", "Value": first_name},
                {"Name": "family_name", "Value": last_name}
            ]
        )

        # 🔑 Cognito User Name (UUID shown in console)
        cognito_user_id = response["UserSub"]

        # 2️⃣ Store user in DB immediately
        db = SessionLocal()
        user = db.query(User).filter(User.email == email).first()

        if not user:
            user = User(
                cognito_user_id=cognito_user_id,
                first_name=first_name,
                last_name=last_name,
                age=age,
                email=email,
                password=password
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
# SIGNIN – VERIFY OTP + CONFIRM USER
# ======================================================
@app.post("/signin")
def signin(email: str, password: str, otp: str):
    try:
        # 1️⃣ Verify OTP
        cognito.confirm_sign_up(
            ClientId=CLIENT_ID,
            Username=email,
            ConfirmationCode=otp
        )

        # 2️⃣ Authenticate (authorization check)
        cognito.initiate_auth(
            ClientId=CLIENT_ID,
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={
                "USERNAME": email,
                "PASSWORD": password
            }
        )

        return {"message": "Signin successful. User verified and confirmed."}

    except cognito.exceptions.CodeMismatchException:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    except cognito.exceptions.ExpiredCodeException:
        raise HTTPException(status_code=400, detail="OTP expired")

    except cognito.exceptions.NotAuthorizedException:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ======================================================
# LOGIN – NORMAL LOGIN
# ======================================================
@app.post("/login")
def login(email: str, password: str):
    try:
        response = cognito.initiate_auth(
            ClientId=CLIENT_ID,
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={
                "USERNAME": email,
                "PASSWORD": password
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

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
def update_user(
    user_id: int,
    first_name: str | None = None,
    last_name: str | None = None,
    age: int | None = None
):
    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if first_name:
        user.first_name = first_name
    if last_name:
        user.last_name = last_name
    if age is not None:
        user.age = age

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
