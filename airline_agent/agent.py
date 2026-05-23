from __future__ import annotations

import re
from datetime import date
from typing import Any

from .models import AgentError, ConversationState, Flight
from .services import AirlineService


TRANSFER_WORDS = ("customer support", "representative", "human", "transfer", "agent", "someone")
POLICY_WORDS = ("refund", "cancel", "cancellation", "change", "reschedule", "baggage", "luggage")


class AirlineBookingAgent:
    def __init__(self, today: date | None = None):
        self.service = AirlineService(today=today)
        self.state = ConversationState()

    def start(self) -> dict[str, Any]:
        return self._reply(
            "Thanks for calling Phonely Airways. I can help book a flight. "
            "Where are you flying from and where are you going?"
        )

    def respond(self, message: str) -> dict[str, Any]:
        text = (message or "").strip()
        if not text:
            return self._reply("I did not catch that. Could you say that again?")

        lowered = text.lower()
        if self._wants_transfer(lowered):
            self.state.stage = "transfer"
            return self._reply(
                "Of course. I will transfer you to customer support now.",
                event="transfer",
                transfer_target="customer_support",
            )

        if self._is_policy_question(lowered):
            return self._reply(self.service.policy_answer(lowered), event="policy_answered")

        if self.state.stage == "collect_trip":
            self._merge_trip_slots(text)
            return self._advance_trip_collection()
        if self.state.stage == "select_flight":
            return self._select_flight(text)
        if self.state.stage == "collect_name":
            self.state.passenger_name = self._extract_name(text)
            return self._advance_passenger_collection()
        if self.state.stage == "collect_contact":
            self.state.contact = self._extract_contact(text)
            return self._book_selected_flight()
        if self.state.stage == "complete":
            return self._reply("The booking is complete. I can help with another trip if you need one.")
        if self.state.stage == "transfer":
            return self._reply("You are being transferred to customer support.")

        self.state.stage = "collect_trip"
        return self._advance_trip_collection()

    def _advance_trip_collection(self) -> dict[str, Any]:
        if not self.state.origin_query:
            return self._reply("What city or airport are you departing from?")
        if not self.state.destination_query:
            return self._reply("And where are you flying to?")
        if not self.state.travel_date_text:
            return self._reply("What date would you like to travel?")

        try:
            flights = self.service.search_flights(
                self.state.origin_query,
                self.state.destination_query,
                self.state.travel_date_text,
            )
        except AgentError as exc:
            self.state.last_error = exc.code
            if exc.code == "UNKNOWN_AIRPORT":
                self.state.origin_query = None
                self.state.destination_query = None
                self.state.travel_date_text = None
                return self._reply(f"{exc.message} Let's start with your departure city.")
            if exc.code == "INVALID_DATE":
                self.state.travel_date_text = None
                return self._reply(f"{exc.message} What travel date should I use?")
            if exc.code == "NO_FLIGHTS":
                self.state.travel_date_text = None
                return self._reply(
                    f"{exc.message} I can search another date or connect you with customer support.",
                    event="no_flights",
                    error=exc.to_dict()["error"],
                )
            return self._reply(exc.message, error=exc.to_dict()["error"])

        self.state.options = flights
        self.state.stage = "select_flight"
        return self._reply(self._format_options(flights), event="flight_options", flights=[f.to_dict() for f in flights])

    def _select_flight(self, text: str) -> dict[str, Any]:
        if not self.state.options:
            self.state.stage = "collect_trip"
            return self._advance_trip_collection()

        selected = self._flight_from_selection(text, self.state.options)
        if not selected:
            return self._reply("Please choose option 1, 2, or 3, or say the flight number.")

        self.state.selected_flight = selected
        self.state.stage = "collect_name"
        return self._reply(
            f"Great, I have {selected.airline} {selected.flight_number}. What is the passenger's full name?",
            event="flight_selected",
            flight=selected.to_dict(),
        )

    def _advance_passenger_collection(self) -> dict[str, Any]:
        if not self.state.passenger_name:
            return self._reply("What is the passenger's full name?")
        self.state.stage = "collect_contact"
        return self._reply("What phone number or email should I send the confirmation to?")

    def _book_selected_flight(self) -> dict[str, Any]:
        if not self.state.selected_flight:
            self.state.stage = "select_flight"
            return self._reply("Which flight option would you like?")
        if not self.state.passenger_name:
            self.state.stage = "collect_name"
            return self._advance_passenger_collection()
        if not self.state.contact:
            self.state.stage = "collect_contact"
            return self._reply("What phone number or email should I send the confirmation to?")

        try:
            booking = self.service.book_flight(
                self.state.selected_flight.flight_id,
                self.state.passenger_name,
                self.state.contact,
            )
        except AgentError as exc:
            if exc.code == "INVALID_PASSENGER":
                self.state.passenger_name = None
                self.state.stage = "collect_name"
                return self._reply(f"{exc.message} What is the passenger's full name?")
            if exc.code == "INVALID_CONTACT":
                self.state.contact = None
                self.state.stage = "collect_contact"
                return self._reply(f"{exc.message} What phone number or email should I use?")
            return self._reply(exc.message, error=exc.to_dict()["error"])

        self.state.stage = "complete"
        channel = "text message" if booking.delivery_channel.value == "sms" else "email"
        return self._reply(
            f"{booking.message} I sent the confirmation by {channel}.",
            event="booking_confirmed",
            booking=booking.to_dict(),
        )

    def _merge_trip_slots(self, text: str) -> None:
        origin, destination = self._extract_route(text)
        if origin:
            self.state.origin_query = origin
        elif self.state.origin_query is None and self._looks_like_place_only(text):
            self.state.origin_query = text

        if destination:
            self.state.destination_query = destination
        elif self.state.origin_query and self.state.destination_query is None and self._looks_like_place_only(text):
            self.state.destination_query = text

        date_text = self._extract_date(text)
        if date_text:
            self.state.travel_date_text = date_text
        elif self.state.origin_query and self.state.destination_query and self.state.travel_date_text is None:
            possible_date = text.strip()
            if re.search(r"\d|today|tomorrow|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec", possible_date, re.I):
                self.state.travel_date_text = possible_date

    def _extract_route(self, text: str) -> tuple[str | None, str | None]:
        match = re.search(
            r"\bfrom\s+(.+?)\s+(?:to|into|toward)\s+(.+?)(?:\s+(?:on|for|leaving|departing)\b|$)",
            text,
            re.I,
        )
        if match:
            return self._clean_slot(match.group(1)), self._clean_slot(match.group(2))

        match = re.search(r"\b(?:to|into|toward)\s+(.+?)(?:\s+(?:from)\s+(.+?))?(?:\s+(?:on|for|leaving|departing)\b|$)", text, re.I)
        if match and match.group(2):
            return self._clean_slot(match.group(2)), self._clean_slot(match.group(1))
        return None, None

    def _extract_date(self, text: str) -> str | None:
        iso = re.search(r"\b\d{4}-\d{2}-\d{2}\b", text)
        if iso:
            return iso.group(0)

        slash = re.search(r"\b\d{1,2}/\d{1,2}(?:/\d{2,4})?\b", text)
        if slash:
            value = slash.group(0)
            if value.count("/") == 1:
                return f"{value}/{self.service.today.year}"
            return value

        relative = re.search(r"\b(today|tomorrow)\b", text, re.I)
        if relative:
            return relative.group(1)

        month = re.search(
            r"\b(january|february|march|april|may|june|july|august|september|october|november|december|"
            r"jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec)\s+\d{1,2}(?:,?\s+\d{4})?\b",
            text,
            re.I,
        )
        if month:
            return month.group(0).replace(",", "")
        return None

    def _extract_name(self, text: str) -> str:
        match = re.search(r"(?:name is|passenger is|for)\s+(.+)$", text, re.I)
        return self._clean_slot(match.group(1) if match else text)

    def _extract_contact(self, text: str) -> str:
        email = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text)
        if email:
            return email.group(0)
        phone = re.search(r"\+?1?[\s.-]?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}", text)
        return phone.group(0) if phone else text.strip()

    def _flight_from_selection(self, text: str, options: list[Flight]) -> Flight | None:
        number = re.search(r"\b([1-9])\b", text)
        if number:
            index = int(number.group(1)) - 1
            if 0 <= index < len(options):
                return options[index]

        normalized = text.upper()
        for flight in options:
            if flight.flight_number.upper() in normalized:
                return flight
        return None

    def _format_options(self, flights: list[Flight]) -> str:
        intro = (
            f"I found {len(flights)} flights from {flights[0].origin.code} to {flights[0].destination.code} "
            f"on {flights[0].travel_date.isoformat()}."
        )
        lines = []
        for idx, flight in enumerate(flights, start=1):
            lines.append(
                f"Option {idx}: {flight.airline} {flight.flight_number}, leaves "
                f"{flight.departure_time.strftime('%H:%M')}, arrives {flight.arrival_time.strftime('%H:%M')}, "
                f"${flight.price_usd}."
            )
        return " ".join([intro, *lines, "Which option would you like?"])

    def _wants_transfer(self, text: str) -> bool:
        return any(word in text for word in TRANSFER_WORDS) and not any(word in text for word in ("flight agent", "booking agent"))

    def _is_policy_question(self, text: str) -> bool:
        return any(word in text for word in POLICY_WORDS)

    def _looks_like_place_only(self, text: str) -> bool:
        return len(text.split()) <= 5 and not any(word in text.lower() for word in ("from", "to", "on", "for", "book", "flight"))

    def _clean_slot(self, value: str) -> str:
        value = re.sub(r"\b(on|for|leaving|departing|please|thanks|thank you)\b.*$", "", value, flags=re.I)
        return re.sub(r"\s+", " ", value.strip(" .,!")).strip()

    def _reply(self, message: str, **extra: Any) -> dict[str, Any]:
        payload: dict[str, Any] = {"message": message, "stage": self.state.stage}
        payload.update(extra)
        return payload
