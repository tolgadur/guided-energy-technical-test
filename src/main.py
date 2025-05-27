from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import requests
import re

from scraper import scrape_all_cities


app = FastAPI()


class LoginRequest(BaseModel):
    email: str
    password: str


@app.get("/")
def read_root():
    return {"message": "Hello, World!"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/login")
def login(request: LoginRequest): # refresh?
    response = requests.post(
        "https://upsx.weather.com/login",
        json={"email": request.email, "password": request.password},
    )
    # Extract the access token from the Set-Cookie header
    raw_cookie = response.headers.get("Set-Cookie")
    token = None
    if raw_cookie:
        match = re.search(r"access_token=([^;]+)", raw_cookie)
        if match:
            token = match.group(1)

    if not token:
        raise ValueError("No access_token found in login response.")

    if not token:
        raise HTTPException(status_code=401, detail="Login failed")

    return {"access_token": token}


@app.get("/scrape-weather")
def scrape_weather():
    all_cities_weather = scrape_all_cities()
    return all_cities_weather


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
