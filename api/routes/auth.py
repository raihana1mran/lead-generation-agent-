from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/auth", tags=["Auth (Mocked)"])

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login")
def login(req: LoginRequest):
    return {"access_token": "mocked_jwt_token", "token_type": "bearer"}

@router.post("/register")
def register(req: LoginRequest):
    return {"message": "User registered successfully"}

@router.post("/logout")
def logout():
    return {"message": "Logged out successfully"}

@router.post("/refresh")
def refresh():
    return {"access_token": "mocked_refresh_token", "token_type": "bearer"}
