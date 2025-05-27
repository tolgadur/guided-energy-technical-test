from fastapi import FastAPI, HTTPException, Cookie
import uvicorn
import requests
import re

from api_types import LoginRequest
from scraper import scrape_all_cities


app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Hello, World!"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/login")
def login(request: LoginRequest):  # todo: token is only valid for 1 hour!
    response = requests.post(
        "https://upsx.weather.com/login",
        json={"email": request.email, "password": request.password},
    )
    # Extract the access token from the Set-Cookie header
    raw_cookie = response.headers.get("Set-Cookie")
    access_token = None
    id_token = None
    refresh_token = None
    if raw_cookie:
        match = re.search(r"access_token=([^;]+)", raw_cookie)
        if match:
            access_token = match.group(1)

        match = re.search(r"id_token=([^;]+)", raw_cookie)
        if match:
            id_token = match.group(1)

        match = re.search(r"refresh_token=([^;]+)", raw_cookie)
        if match:
            refresh_token = match.group(1)

    if not access_token or not id_token or not refresh_token:
        raise HTTPException(status_code=401, detail="Login failed")

    return {"id_token": id_token}


@app.get("/scrape-weather")
def scrape_weather():
    all_cities_weather = scrape_all_cities()
    return all_cities_weather


@app.get("/favorites")
def get_favorites(id_token: str = Cookie(...)):
    url = "https://upsx.weather.com/preference"
    response = requests.get(url, cookies={"id_token": id_token})
    if response.status_code != 200:
        print("Status:", response.status_code)
        print("Response text:", response.text)
        print("Response headers:", response.headers)
        raise HTTPException(status_code=401, detail="Unauthorized")

    # get favourite cities
    try:
        locations = response.json()["locations"]
        favourite_cities = [loc["name"] for loc in locations]
    except (KeyError, IndexError):
        print(f"{response.json()=}")
        raise HTTPException(status_code=500, detail="Unexpected response structure")

    return {"favorites": favourite_cities}



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
