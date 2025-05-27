from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    password: str


class AddFavouriteRequest(BaseModel):
    authentication_token: str
