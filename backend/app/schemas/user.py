from pydantic import BaseModel, ConfigDict


class UserCreate(BaseModel):
    company_id: str
    email: str
    password: str


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    company_id: str
    email: str
    role: str
    is_active: bool


class LoginRequest(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
