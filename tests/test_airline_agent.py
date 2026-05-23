from __future__ import annotations

import json
import threading
import unittest
from datetime import date
from http.client import HTTPConnection

from airline_agent.agent import AirlineBookingAgent
from airline_agent.models import AgentError
from airline_agent.server import build_server
from airline_agent.services import AirlineService


class AirlineServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.service = AirlineService(today=date(2026, 5, 23))

    def test_resolves_city_to_iata(self) -> None:
        self.assertEqual(self.service.resolve_airport("Los Angeles").code, "LAX")
        self.assertEqual(self.service.resolve_airport("new york").code, "JFK")

    def test_invalid_date_is_rejected(self) -> None:
        with self.assertRaises(AgentError) as context:
            self.service.search_flights("LAX", "JFK", "2025-01-01")
        self.assertEqual(context.exception.code, "INVALID_DATE")

    def test_no_flights_aal_to_yvr_returns_404_error(self) -> None:
        with self.assertRaises(AgentError) as context:
            self.service.search_flights("AAL", "YVR", "2026-06-12")
        self.assertEqual(context.exception.code, "NO_FLIGHTS")
        self.assertEqual(context.exception.status, 404)

    def test_booking_routes_us_phone_to_sms(self) -> None:
        flight = self.service.search_flights("Los Angeles", "New York", "2026-06-12")[0]
        booking = self.service.book_flight(flight.flight_id, "Sarah Zhang", "+1 415 555 0199")
        self.assertEqual(booking.delivery_channel.value, "sms")
        self.assertIn("Confirmation PN", booking.message)

    def test_booking_routes_email_otherwise(self) -> None:
        flight = self.service.search_flights("LAX", "JFK", "2026-06-12")[0]
        booking = self.service.book_flight(flight.flight_id, "Sarah Zhang", "sarah@example.com")
        self.assertEqual(booking.delivery_channel.value, "email")


class AirlineAgentTest(unittest.TestCase):
    def test_happy_path_conversation(self) -> None:
        agent = AirlineBookingAgent(today=date(2026, 5, 23))
        response = agent.respond("I need to fly from Los Angeles to New York on June 12 2026")
        self.assertEqual(response["event"], "flight_options")

        response = agent.respond("option 1")
        self.assertEqual(response["event"], "flight_selected")

        response = agent.respond("Sarah Zhang")
        self.assertEqual(response["stage"], "collect_contact")

        response = agent.respond("+1 415 555 0199")
        self.assertEqual(response["event"], "booking_confirmed")
        self.assertEqual(response["booking"]["delivery_channel"], "sms")

    def test_transfer_interrupt(self) -> None:
        agent = AirlineBookingAgent(today=date(2026, 5, 23))
        response = agent.respond("Please put me through to customer support")
        self.assertEqual(response["event"], "transfer")
        self.assertEqual(response["transfer_target"], "customer_support")

    def test_policy_answer(self) -> None:
        agent = AirlineBookingAgent(today=date(2026, 5, 23))
        response = agent.respond("What is the refund policy?")
        self.assertEqual(response["event"], "policy_answered")
        self.assertIn("Refundable fares", response["message"])


class ServerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = build_server(0)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()

    def post_json(self, path: str, payload: dict[str, str]) -> tuple[int, dict]:
        connection = HTTPConnection("127.0.0.1", self.port)
        connection.request("POST", path, body=json.dumps(payload), headers={"content-type": "application/json"})
        response = connection.getresponse()
        data = json.loads(response.read().decode("utf-8"))
        connection.close()
        return response.status, data

    def test_flights_endpoint(self) -> None:
        status, data = self.post_json(
            "/flights",
            {"origin": "LAX", "destination": "JFK", "date": "2026-06-12"},
        )
        self.assertEqual(status, 200)
        self.assertGreaterEqual(len(data["flights"]), 2)

    def test_no_flights_endpoint_uses_404(self) -> None:
        status, data = self.post_json(
            "/flights",
            {"origin": "AAL", "destination": "YVR", "date": "2026-06-12"},
        )
        self.assertEqual(status, 404)
        self.assertEqual(data["error"]["code"], "NO_FLIGHTS")


if __name__ == "__main__":
    unittest.main()
