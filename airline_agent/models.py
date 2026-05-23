from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, time
from enum import Enum
from typing import Any


class AgentError(Exception):
    def __init__(self, code: str, message: str, status: int = 400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status

    def to_dict(self) -> dict[str, Any]:
        return {"error": {"code": self.code, "message": self.message}}


class DeliveryChannel(str, Enum):
    SMS = "sms"
    EMAIL = "email"


@dataclass(frozen=True)
class Airport:
    code: str
    name: str
    city: str
    country: str
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class RouteOption:
    airline: str
    flight_number: str
    departure_time: time
    arrival_time: time
    price_usd: int
    seats_remaining: int


@dataclass(frozen=True)
class Flight:
    flight_id: str
    airline: str
    flight_number: str
    origin: Airport
    destination: Airport
    travel_date: date
    departure_time: time
    arrival_time: time
    price_usd: int
    seats_remaining: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "flight_id": self.flight_id,
            "airline": self.airline,
            "flight_number": self.flight_number,
            "origin": self.origin.code,
            "origin_city": self.origin.city,
            "destination": self.destination.code,
            "destination_city": self.destination.city,
            "date": self.travel_date.isoformat(),
            "departure_time": self.departure_time.strftime("%H:%M"),
            "arrival_time": self.arrival_time.strftime("%H:%M"),
            "price_usd": self.price_usd,
            "seats_remaining": self.seats_remaining,
        }


@dataclass(frozen=True)
class Passenger:
    full_name: str
    contact: str

    def to_dict(self) -> dict[str, str]:
        return {"full_name": self.full_name, "contact": self.contact}


@dataclass(frozen=True)
class Booking:
    confirmation_number: str
    flight: Flight
    passenger: Passenger
    delivery_channel: DeliveryChannel
    delivery_target: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "confirmation_number": self.confirmation_number,
            "flight": self.flight.to_dict(),
            "passenger": self.passenger.to_dict(),
            "delivery_channel": self.delivery_channel.value,
            "delivery_target": self.delivery_target,
            "message": self.message,
        }


@dataclass
class ConversationState:
    origin_query: str | None = None
    destination_query: str | None = None
    travel_date_text: str | None = None
    origin: Airport | None = None
    destination: Airport | None = None
    travel_date: date | None = None
    options: list[Flight] = field(default_factory=list)
    selected_flight: Flight | None = None
    passenger_name: str | None = None
    contact: str | None = None
    stage: str = "collect_trip"
    last_error: str | None = None
