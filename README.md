# Airline Booking AI Agent

This repo contains a runnable agent for Phonely's airline-booking assignment. It includes:

- A deterministic voice-agent conversation engine.
- A simple airport assistant with flight availability search, booking, and confirmation delivery.
- An HTTP API that can be wired to Phonely API Request blocks.
- Phonely-ready guidelines, workflow notes, knowledge base copy, and a Postman collection.

## Quick Start

```bash
python3 -m unittest discover -s tests
python3 -m airline_agent.cli
```

Run the local API server:

```bash
python3 -m airline_agent.server --port 8080
```

Then try:

```bash
curl -s http://localhost:8080/health
curl -s -X POST http://localhost:8080/flights \
  -H 'content-type: application/json' \
  -d '{"origin":"Los Angeles","destination":"New York","date":"2026-06-12"}'
```

## Main Agent Flow

1. Resolve departure and destination city or airport names into IATA codes.
2. Validate the travel date. It must be today or within the next year.
3. Search mock flight inventory and present multiple options.
4. Collect the passenger's name and contact info.
5. Book the selected flight and generate a confirmation number.
6. Send confirmation by SMS for US phone numbers and email otherwise.
7. Transfer immediately if the caller asks for customer support.
8. Answer refund and change-policy questions from the knowledge base.