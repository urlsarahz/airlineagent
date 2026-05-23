# Phonely Flow Blueprint

This flow is designed for Phonely's visual builder using Talk, API Request, Filter, SMS, Email, Transfer, and End Call blocks.

## 1. Greeting Talk Block

Say:

"Thanks for calling Phonely Airways. I can help book a flight. Where are you flying from and where are you going?"

Global interruption rule:

- If caller asks for support, a representative, a human, or transfer, route to the Transfer block immediately.

## 2. Search Flights API Request

Endpoint:

`POST https://your-host.example.com/flights`

Body:

```json
{
  "origin": "@origin",
  "destination": "@destination",
  "date": "@travel_date"
}
```

Auto-gather variables:

- `origin`: Text, required, description "Departure city or airport code."
- `destination`: Text, required, description "Destination city or airport code."
- `travel_date`: Date or custom ISO date, required, description "Travel date, today through one year from today."

Success path:

- Store `flights`.
- Present numbered options with airline, flight number, time, and price.

Failure paths:

- `UNKNOWN_AIRPORT`: ask for the city or three-letter code again.
- `INVALID_DATE`: ask for another date.
- `NO_FLIGHTS`: tell the caller no flights are available, then offer another date or support transfer.

## 3. Flight Selection Talk/Collect Block

Ask:

"Which option would you like?"

Store:

- `selected_flight_id`
- `selected_airline`
- `selected_flight_number`
- `selected_price`

If the caller gives an invalid option, ask again using the option numbers.

## 4. Booking API Request

Endpoint:

`POST https://your-host.example.com/book`

Body:

```json
{
  "flight_id": "@selected_flight_id",
  "passenger_name": "@passenger_name",
  "contact": "@contact"
}
```

Auto-gather variables:

- `passenger_name`: Text, required, confirm, spell back if needed.
- `contact`: Email or custom contact, required, confirm.

Success response variables:

- `confirmation_number`
- `delivery_channel`
- `delivery_target`
- `message`

## 5. Send Confirmation

Filter:

- If `delivery_channel` equals `sms`, use SMS block.
- Otherwise use Email block.

Message:

Use the `message` value from the booking response, including the departure, destination, airline, flight number, and confirmation number.

## 6. End Call

Say:

"You are all set. Your confirmation number is @confirmation_number. Thanks for flying with Phonely Airways."

## 7. Transfer Block

Use a warm transfer target named `customer_support`.

Say:

"Of course. I will transfer you to customer support now."
