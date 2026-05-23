# Airline Agent API Contract

Base URL for local testing:

`http://127.0.0.1:8080`

## GET /health

Returns service status.

## POST /resolve-airport

Request:

```json
{ "query": "Los Angeles" }
```

Response:

```json
{
  "airport": {
    "code": "LAX",
    "name": "Los Angeles International Airport",
    "city": "Los Angeles",
    "country": "United States",
    "aliases": ["los angeles", "la"]
  }
}
```

## POST /flights

Request:

```json
{
  "origin": "Los Angeles",
  "destination": "New York",
  "date": "2026-06-12"
}
```

Success response:

```json
{
  "flights": [
    {
      "flight_id": "LAX-JFK-2026-06-12-PX101",
      "airline": "Pacific Air",
      "flight_number": "PX101",
      "origin": "LAX",
      "destination": "JFK",
      "date": "2026-06-12",
      "departure_time": "07:45",
      "arrival_time": "16:10",
      "price_usd": 289,
      "seats_remaining": 7
    }
  ]
}
```

No flights response:

```json
{
  "error": {
    "code": "NO_FLIGHTS",
    "message": "No flights are available from AAL to YVR on 2026-06-12."
  }
}
```

## POST /book

Request:

```json
{
  "flight_id": "LAX-JFK-2026-06-12-PX101",
  "passenger_name": "Sarah Zhang",
  "contact": "+1 415 555 0199"
}
```

Response:

```json
{
  "booking": {
    "confirmation_number": "PN123ABC",
    "delivery_channel": "sms",
    "delivery_target": "+14155550199",
    "message": "Confirmed: Sarah Zhang is booked..."
  }
}
```

## POST /policy

Request:

```json
{ "topic": "refund policy" }
```

Response:

```json
{ "answer": "Refundable fares can be refunded..." }
```

## POST /agent/respond

Local conversational test endpoint.

Request:

```json
{
  "session_id": "demo",
  "message": "I need to fly from Los Angeles to New York on June 12 2026"
}
```
