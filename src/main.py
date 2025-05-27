from fastapi import FastAPI
import uvicorn

from scraper import scrape_all_cities


app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/scrape-weather")
def scrape_weather():
    all_cities_weather = scrape_all_cities()
    return all_cities_weather


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
