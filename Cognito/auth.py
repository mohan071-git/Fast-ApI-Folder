from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr
import boto3
import requests
from jose import jwt

app = FastAPI(title="FastAPI + AWS Cognito")

# ===== COGNITO CONFIG =====
REGION = "eu-north-1"
USER_POOL_ID = "eu-north-1_1iAJ6sP4z"
CLIENT_ID = "6532e06a9m6e9i3g4ehm5omp4g"  # NO CLIENT SECRET

cognito = boto3.client("cognito-idp", region_name=REGION)

# ===== SCHEMAS =====
class SignUpSchema(BaseModel):
    email: EmailStr
    password: str

class LoginSchema(BaseModel):
    email: EmailStr
    password: str

# ===== SIGNUP =====
@app.post("/signup")
def signup(data: SignUpSchema):
    try:
        cognito.sign_up(
            ClientId=CLIENT_ID,
            Username=data.email,
            Password=data.password,
            UserAttributes=[
                {"Name": "email", "Value": data.email}
            ]
        )
        return {"message": "Signup successful. Check email for verification code."}

    except cognito.exceptions.UsernameExistsException:
        raise HTTPException(status_code=400, detail="User already exists")

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ===== LOGIN =====
@app.post("/login")
def login(data: LoginSchema):
    try:
        response = cognito.initiate_auth(
            ClientId=CLIENT_ID,
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={
                "USERNAME": data.email,
                "PASSWORD": data.password
            }
        )

        auth = response["AuthenticationResult"]

        return {
            "access_token": auth["AccessToken"],
            "id_token": auth["IdToken"],
            "refresh_token": auth["RefreshToken"],
            "token_type": "bearer"
        }

    except cognito.exceptions.NotAuthorizedException:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
