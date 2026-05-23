from __future__ import annotations

import hashlib
import re
from datetime import date, datetime, timedelta

from .data import AIRPORTS, POLICIES, ROUTES
from .models import AgentError, Airport, Booking, DeliveryChannel, Flight, Passenger


AIRPORT_BY_CODE = {airport.code: airport for airport in AIRPORTS}


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", " ", text.lower())).strip()


class AirlineService:
    def __init__(self, today: date | None = None):
        self.today = today or date.today()

    def resolve_airport(self, query: str) -> Airport:
        if not query or not query.strip():
            raise AgentError("UNKNOWN_AIRPORT", "Please provide a city or airport name.", 422)

        raw = query.strip()
        code = raw.upper()
        if code in AIRPORT_BY_CODE:
            return AIRPORT_BY_CODE[code]

        normalized = _normalize(raw)
        matches: list[Airport] = []
        for airport in AIRPORTS:
            terms = (airport.city, airport.name, airport.code, *airport.aliases)
            if any(_normalize(term) == normalized for term in terms):
                matches.append(airport)

        if len(matches) == 1:
            return matches[0]

        partials = [
            airport
            for airport in AIRPORTS
            if normalized and any(normalized in _normalize(term) for term in (airport.city, airport.name, *airport.aliases))
        ]
        if len(partials) == 1:
            return partials[0]

        raise AgentError(
            "UNKNOWN_AIRPORT",
            f"I could not find an airport for '{query}'. Please say the city or three-letter airport code.",
            422,
        )

    def validate_travel_date(self, value: str) -> date:
        if not value or not value.strip():
            raise AgentError("INVALID_DATE", "Please provide a travel date.", 400)

        text = value.strip().lower()
        if text == "today":
            parsed = self.today
        elif text == "tomorrow":
            parsed = self.today + timedelta(days=1)
        else:
            parsed = self._parse_date_text(text)

        latest = self.today + timedelta(days=365)
        if parsed < self.today or parsed > latest:
            raise AgentError(
                "INVALID_DATE",
                f"Travel date must be between {self.today.isoformat()} and {latest.isoformat()}.",
                400,
            )
        return parsed

    def search_flights(self, origin_query: str, destination_query: str, travel_date_text: str) -> list[Flight]:
        origin = self.resolve_airport(origin_query)
        destination = self.resolve_airport(destination_query)
        travel_date = self.validate_travel_date(travel_date_text)

        if origin.code == destination.code:
            raise AgentError("INVALID_ROUTE", "Departure and destination airports must be different.", 400)

        route_options = ROUTES.get((origin.code, destination.code), ())
        if not route_options:
            raise AgentError(
                "NO_FLIGHTS",
                f"No flights are available from {origin.code} to {destination.code} on {travel_date.isoformat()}.",
                404,
            )

        return [
            Flight(
                flight_id=f"{origin.code}-{destination.code}-{travel_date.isoformat()}-{option.flight_number}",
                airline=option.airline,
                flight_number=option.flight_number,
                origin=origin,
                destination=destination,
                travel_date=travel_date,
                departure_time=option.departure_time,
                arrival_time=option.arrival_time,
                price_usd=option.price_usd,
                seats_remaining=option.seats_remaining,
            )
            for option in route_options
        ]

    def book_flight(self, flight_id: str, passenger_name: str, contact: str) -> Booking:
        flight = self.get_flight_by_id(flight_id)
        passenger = self._build_passenger(passenger_name, contact)
        channel = self.delivery_channel_for(passenger.contact)
        confirmation = self._confirmation_number(flight.flight_id, passenger.full_name, passenger.contact)
        message = self._confirmation_message(confirmation, flight, passenger)
        return Booking(
            confirmation_number=confirmation,
            flight=flight,
            passenger=passenger,
            delivery_channel=channel,
            delivery_target=passenger.contact,
            message=message,
        )

    def get_flight_by_id(self, flight_id: str) -> Flight:
        match = re.fullmatch(r"([A-Z]{3})-([A-Z]{3})-(\d{4}-\d{2}-\d{2})-([A-Z]{2}\d{3})", flight_id.strip())
        if not match:
            raise AgentError("UNKNOWN_FLIGHT", "The selected flight could not be found.", 404)

        origin, destination, travel_date_text, flight_number = match.groups()
        flights = self.search_flights(origin, destination, travel_date_text)
        for flight in flights:
            if flight.flight_number == flight_number:
                return flight
        raise AgentError("UNKNOWN_FLIGHT", "The selected flight could not be found.", 404)

    def policy_answer(self, topic: str) -> str:
        normalized = _normalize(topic)
        if any(word in normalized for word in ("refund", "cancel", "cancellation")):
            return POLICIES["refund"]
        if any(word in normalized for word in ("change", "reschedule", "modify")):
            return POLICIES["change"]
        if any(word in normalized for word in ("bag", "baggage", "luggage")):
            return POLICIES["baggage"]
        return (
            "I can help with booking, changes, refunds, and baggage policies. "
            "For anything more complex, I can connect you with customer support."
        )

    def delivery_channel_for(self, contact: str) -> DeliveryChannel:
        if self._is_us_phone(contact):
            return DeliveryChannel.SMS
        if self._is_email(contact):
            return DeliveryChannel.EMAIL
        raise AgentError("INVALID_CONTACT", "Please provide a US phone number or an email address.", 400)

    def _parse_date_text(self, text: str) -> date:
        formats = ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%B %d %Y", "%b %d %Y", "%B %d", "%b %d")
        for fmt in formats:
            try:
                parsed_dt = datetime.strptime(text, fmt)
            except ValueError:
                continue

            parsed = parsed_dt.date()
            if "%Y" not in fmt and "%y" not in fmt:
                parsed = parsed.replace(year=self.today.year)
                if parsed < self.today:
                    parsed = parsed.replace(year=self.today.year + 1)
            return parsed

        raise AgentError(
            "INVALID_DATE",
            "Please use a clear date such as 2026-06-12, June 12 2026, today, or tomorrow.",
            400,
        )

    def _build_passenger(self, passenger_name: str, contact: str) -> Passenger:
        name = re.sub(r"\s+", " ", passenger_name or "").strip()
        if len(name.split()) < 2:
            raise AgentError("INVALID_PASSENGER", "Please provide the passenger's full name.", 400)
        clean_contact = re.sub(r"\s+", "", contact or "").strip()
        self.delivery_channel_for(clean_contact)
        return Passenger(full_name=name, contact=clean_contact)

    def _confirmation_number(self, flight_id: str, name: str, contact: str) -> str:
        seed = f"{flight_id}|{name.lower()}|{contact.lower()}"
        digest = hashlib.sha1(seed.encode("utf-8")).hexdigest().upper()
        return f"PN{digest[:6]}"

    def _confirmation_message(self, confirmation: str, flight: Flight, passenger: Passenger) -> str:
        return (
            f"Confirmed: {passenger.full_name} is booked on {flight.airline} {flight.flight_number} "
            f"from {flight.origin.code} to {flight.destination.code} on {flight.travel_date.isoformat()} "
            f"at {flight.departure_time.strftime('%H:%M')}. Confirmation {confirmation}."
        )

    @staticmethod
    def _is_email(value: str) -> bool:
        return re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value or "") is not None

    @staticmethod
    def _is_us_phone(value: str) -> bool:
        digits = re.sub(r"\D", "", value or "")
        return len(digits) == 10 or (len(digits) == 11 and digits.startswith("1"))
