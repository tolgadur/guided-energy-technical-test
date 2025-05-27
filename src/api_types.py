from typing import List
from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    password: str


class AddFavoriteRequest(BaseModel):
    favorite_cities: List[str]
