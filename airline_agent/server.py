from __future__ import annotations

import argparse
import json
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse

from .agent import AirlineBookingAgent
from .models import AgentError
from .services import AirlineService


class AgentRegistry:
    def __init__(self) -> None:
        self.sessions: dict[str, AirlineBookingAgent] = {}

    def get(self, session_id: str) -> AirlineBookingAgent:
        if session_id not in self.sessions:
            self.sessions[session_id] = AirlineBookingAgent()
        return self.sessions[session_id]


class AirlineRequestHandler(BaseHTTPRequestHandler):
    service = AirlineService()
    agents = AgentRegistry()

    def do_OPTIONS(self) -> None:
        self._send_json({"ok": True})

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/health":
            self._send_json({"status": "ok", "service": "airline-booking-agent"})
            return
        self._send_json({"error": {"code": "NOT_FOUND", "message": "Route not found."}}, status=404)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        try:
            body = self._read_json()
            if path == "/resolve-airport":
                airport = self.service.resolve_airport(str(body.get("query", "")))
                self._send_json({"airport": airport.__dict__})
            elif path == "/flights":
                flights = self.service.search_flights(
                    str(body.get("origin", "")),
                    str(body.get("destination", "")),
                    str(body.get("date", "")),
                )
                self._send_json({"flights": [flight.to_dict() for flight in flights]})
            elif path == "/book":
                booking = self.service.book_flight(
                    str(body.get("flight_id", "")),
                    str(body.get("passenger_name", "")),
                    str(body.get("contact", "")),
                )
                self._send_json({"booking": booking.to_dict()})
            elif path == "/notify":
                self._send_json({"sent": True, "note": "Mock notification accepted.", "request": body})
            elif path == "/policy":
                self._send_json({"answer": self.service.policy_answer(str(body.get("topic", "")))})
            elif path == "/agent/respond":
                session_id = str(body.get("session_id", "default"))
                agent = self.agents.get(session_id)
                message = str(body.get("message", ""))
                self._send_json(agent.respond(message))
            else:
                self._send_json({"error": {"code": "NOT_FOUND", "message": "Route not found."}}, status=404)
        except AgentError as exc:
            self._send_json(exc.to_dict(), status=exc.status)
        except json.JSONDecodeError:
            self._send_json({"error": {"code": "BAD_JSON", "message": "Request body must be valid JSON."}}, status=400)

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("content-length", "0"))
        raw = self.rfile.read(length).decode("utf-8") if length else "{}"
        return json.loads(raw or "{}")

    def _send_json(self, payload: dict[str, Any], status: int = 200) -> None:
        encoded = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("access-control-allow-origin", "*")
        self.send_header("access-control-allow-methods", "GET,POST,OPTIONS")
        self.send_header("access-control-allow-headers", "content-type")
        self.send_header("content-length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def build_server(port: int) -> ThreadingHTTPServer:
    return ThreadingHTTPServer(("127.0.0.1", port), AirlineRequestHandler)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the airline booking agent API.")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    server = build_server(args.port)
    print(f"Airline booking agent API listening on http://127.0.0.1:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
