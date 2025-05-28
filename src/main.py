from typing import List
from fastapi import FastAPI, HTTPException, Cookie
import uvicorn
import requests
import re

from api_types import LoginRequest, AddFavoriteRequest, AskRequest, AskResponse
from scraper import (
    scrape_all_cities,
    get_city_data,
    scrape_weather as scrape_weather_for_city,
)
from db import (
    create_db_and_tables,
    store_new_favorite_cities,
    get_favourite_cities,
    FavoriteCity,
)
from llm import ask_gpt

app = FastAPI()


def build_weather_context(cities: List[FavoriteCity]) -> str:
    return "\n".join(
        f"{city.name}: {city.temperature}°C, {city.weather_condition}"
        for city in cities
    )


def get_favourite_cities_from_scraped_location(locations: list[dict]):
    ids = set()
    favourite_cities = []
    for loc in locations:
        name = loc["name"]
        place_id = loc["placeID"]
        if place_id in ids:
            continue
        ids.add(place_id)
        weather = scrape_weather_for_city(name, place_id)
        favourite_cities.append(
            {
                "city": name,
                "placeID": place_id,
                "condition": weather["condition"],
                "position": loc["position"],
                "coordinate": loc["coordinate"],
                "temperature": weather["temperature"],
            }
        )
    return favourite_cities


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
    locations = response.json().get("locations", [])
    favourite_cities = get_favourite_cities_from_scraped_location(locations)
    store_new_favorite_cities(favourite_cities)

    return {"favorites": favourite_cities}


@app.post("/favorites")
def add_favorite(request: AddFavoriteRequest, id_token: str = Cookie(...)):
    url = "https://upsx.weather.com/preference"
    response = requests.get(url, cookies={"id_token": id_token})
    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="Unauthorized")

    data = response.json()
    locations = data.get("locations", [])
    counter = len(locations)

    for city in request.favorite_cities:
        city_data = get_city_data(city, id_token, counter)
        locations.append(city_data)
        counter += 1

    print("Putting new data in.")
    data["locations"] = locations
    response = requests.put(url, json=data, cookies={"id_token": id_token})
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    print("Storing new data in db.")
    favourite_cities = get_favourite_cities_from_scraped_location(locations)
    store_new_favorite_cities(favourite_cities)

    return {"favourite_cities": favourite_cities}


@app.get("/summary")
def get_summary():
    favourite_cities = get_favourite_cities()
    weather_context = build_weather_context(favourite_cities)
    prompt = (
        "Give me a one-sentence summary of the weather in the following cities: "
        + weather_context
        + ". For example: 'It's sunny in London and Manchester, rainy in Birmingham.'"
    )
    summary = ask_gpt(prompt)

    return {"summary": summary}


@app.post("/ask", response_model=AskResponse)
def ask_about_favourite_cities(request: AskRequest):
    favourite_cities = get_favourite_cities()
    weather_context = build_weather_context(favourite_cities)
    prompt = (
        f"Here is the weather data: {weather_context} "
        + f"answer the following question: {request.query}"
    )
    answer = ask_gpt(prompt)

    # extract matching cities from answer
    city_names = [city.name for city in favourite_cities]
    matching_cities = [name for name in city_names if name.lower() in answer.lower()]

    return AskResponse(answer=answer, matching_cities=matching_cities)


if __name__ == "__main__":
    create_db_and_tables()
    print("DB created.")
    uvicorn.run(app, host="0.0.0.0", port=8000)
