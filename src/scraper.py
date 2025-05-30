import requests
from bs4 import BeautifulSoup
import re
from fastapi import HTTPException

CITY_CODES = {
    "London": "0b8697c01baca04214b4abd206319d3eba60db5fb05c191012c4e02f6bdb23a4",
    "Birmingham": "e22e5ef714ce1dd78d0094a96eca7a476b97d17e3d4b99aaa7e84971e35911c8",
    "Manchester": "ee3ce32cd070f384eba06807c25f3025e5d5ba3546b4112f3f1275b802fc36a7",
    "Glasgow": "5683ac40db769e80dbb4b5ffb3e79772b9e1a82d2acae79b93ae10ec9b8fb2e0",
    "Leeds": "a908f589d9779db06b12365cb9926fdee43ec56adc04a39c8a425e29714bb8d9",
}


def scrape_weather(city: str, location_code: str):
    url = f"https://weather.com/en-GB/weather/hourbyhour/l/{location_code}?unit=m"
    soup = BeautifulSoup(requests.get(url).text, "lxml")
    weather = soup.find(id=re.compile("detailIndex0$"))
    if not weather:
        raise ValueError("Could not find weather details.")

    condition = weather.find("title").get_text(strip=True).lower()
    temp_str = weather.find("span", {"data-testid": "TemperatureValue"}).get_text(
        strip=True
    )
    temperature = int(temp_str.rstrip("°"))

    return {
        "city": city,
        "condition": condition,
        "temperature": temperature,
    }


def scrape_all_cities():
    results = []
    for city, code in CITY_CODES.items():
        try:
            weather = scrape_weather(city, code)
            results.append(weather)
        except Exception as e:
            print(f"Failed to get weather for {city}: {e}")
    return results


def get_city_data(city: str, id_token: str, position: int):
    url = "https://weather.com/api/v1/p/redux-dal"
    payload = [
        {
            "name": "getSunV3LocationSearchUrlConfig",
            "params": {
                "query": city,
                "language": "en-GB",
                "locationType": "locale",
            },
        }
    ]
    response = requests.post(url, cookies={"id_token": id_token}, json=payload)
    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # build response
    data = response.json()["dal"]["getSunV3LocationSearchUrlConfig"]
    for result in data.values():
        if result.get("loaded") and "data" in result:
            location = result["data"]["location"]
            response_data = {
                "name": location["displayName"][0],
                "coordinate": f"{location['latitude'][0]},{location['longitude'][0]}",
                "placeID": location["placeId"][0],
                "position": position,
            }
            return response_data

    raise HTTPException(status_code=404, detail="No location data found")
