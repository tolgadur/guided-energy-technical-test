import requests
from bs4 import BeautifulSoup
import re


def scrape_london_weather():
    url = "https://weather.com/en-GB/weather/hourbyhour/l/0b8697c01baca04214b4abd206319d3eba60db5fb05c191012c4e02f6bdb23a4?unit=m"
    soup = BeautifulSoup(requests.get(url).text, "lxml")
    weather = soup.find(id=re.compile("detailIndex0$"))
    if not weather:
        raise ValueError("Could not find weather details.")

    city = "London"
    condition = weather.find("title").get_text(strip=True).lower()
    temp_str = weather.find("span", {"data-testid": "TemperatureValue"}).get_text(strip=True)
    temperature = int(temp_str.rstrip("°"))

    return {
        "city": city,
        "condition": condition,
        "temperature": temperature,
    }


def main():
    london_weather = scrape_london_weather()
    print(london_weather)


if __name__ == "__main__":
    main()
