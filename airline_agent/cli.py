from __future__ import annotations

from .agent import AirlineBookingAgent


def main() -> None:
    agent = AirlineBookingAgent()
    print(agent.start()["message"])
    while True:
        try:
            user_input = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if user_input.lower() in {"quit", "exit"}:
            break
        response = agent.respond(user_input)
        print(response["message"])


if __name__ == "__main__":
    main()
