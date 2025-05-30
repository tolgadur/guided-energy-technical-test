# This is some basic readme for the challenge

You need to set your OpenAI API key in an environment variable called `OPENAI_API_KEY`. 

## How would I scale this?

Bunch of issues in this naive approach. Amongst others:

- only works for one user
- will face ratelimiting issues and other mechanisms to stop scraping

If I wanted to scrape all of weather.com regularly I would:

1. Save mapping of location ids and some metadata that doesn't change like latitude, longitude etc. in a db and cache like Redis.
2. Use Terraform to provision N short lived nodes. Probably on Hetzner Cloud as this is super cheap. N would depend on some empirical tests,
3. Split the location ids into N buckets with a hash-function. Call each nodes with the subset of locaiton ids it needs to scrape.
4. Each node scrapes it's subset in an async fashion and sends it into a queue like Kafka. The short lived nodes are then shut down via Terraform.
5. Some async process collects the items in the Queue and stores them in my actual database.

## Example requests

Here are some example requests. You can find more extensive, prettier docs in the autogenerated OpenAPI documentation:

Login request:

```json
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"email":"EMAIL","password":"PASSWORD"}'
```

Get favourites:

```json
curl -X GET  http://localhost:8000/favorites \
-b "id_token=ID_TOKEN"
```

Add favourites:

```json
curl -X POST http://localhost:8000/favorites \
-H "Content-Type: application/json" \
-b "id_token=ID_TOKEN"
-d '{"favorite_cities": ["birmingham", "paris"]}'
```

Summary request:

```json
curl -X GET http://localhost:8000/summary
```

Ask about favourite cities:

```json
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "Which cities have sunny weather now so that I can go sunbathing?"}'
```
