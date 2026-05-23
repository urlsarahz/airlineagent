from __future__ import annotations

from datetime import time

from .models import Airport, RouteOption


AIRPORTS: tuple[Airport, ...] = (
    Airport("AAL", "Aalborg Airport", "Aalborg", "Denmark", ("aalborg",)),
    Airport("ATL", "Hartsfield-Jackson Atlanta International Airport", "Atlanta", "United States", ("atlanta",)),
    Airport("BOS", "Boston Logan International Airport", "Boston", "United States", ("boston", "logan")),
    Airport("DEN", "Denver International Airport", "Denver", "United States", ("denver",)),
    Airport("DFW", "Dallas Fort Worth International Airport", "Dallas", "United States", ("dallas", "fort worth")),
    Airport("JFK", "John F. Kennedy International Airport", "New York", "United States", ("new york", "nyc", "john f kennedy")),
    Airport("LAS", "Harry Reid International Airport", "Las Vegas", "United States", ("las vegas", "vegas")),
    Airport("LAX", "Los Angeles International Airport", "Los Angeles", "United States", ("los angeles", "la")),
    Airport("MIA", "Miami International Airport", "Miami", "United States", ("miami",)),
    Airport("ORD", "Chicago O'Hare International Airport", "Chicago", "United States", ("chicago", "ohare", "o hare")),
    Airport("SEA", "Seattle-Tacoma International Airport", "Seattle", "United States", ("seattle", "seatac", "sea tac")),
    Airport("SFO", "San Francisco International Airport", "San Francisco", "United States", ("san francisco", "sf", "bay area")),
    Airport("YVR", "Vancouver International Airport", "Vancouver", "Canada", ("vancouver",)),
)


ROUTES: dict[tuple[str, str], tuple[RouteOption, ...]] = {
    ("LAX", "JFK"): (
        RouteOption("Pacific Air", "PX101", time(7, 45), time(16, 10), 289, 7),
        RouteOption("Coastline Airways", "CL432", time(12, 30), time(20, 55), 318, 5),
        RouteOption("Nimbus Air", "NB908", time(21, 15), time(5, 40), 251, 3),
    ),
    ("JFK", "LAX"): (
        RouteOption("Pacific Air", "PX102", time(8, 20), time(11, 40), 301, 6),
        RouteOption("Coastline Airways", "CL433", time(17, 10), time(20, 30), 276, 4),
    ),
    ("SFO", "SEA"): (
        RouteOption("Cascade Jet", "CJ220", time(9, 5), time(11, 10), 142, 8),
        RouteOption("Pacific Air", "PX330", time(18, 25), time(20, 35), 166, 9),
    ),
    ("SEA", "LAX"): (
        RouteOption("Cascade Jet", "CJ221", time(6, 55), time(9, 35), 188, 6),
        RouteOption("Nimbus Air", "NB441", time(14, 40), time(17, 20), 207, 2),
    ),
    ("LAX", "SFO"): (
        RouteOption("Pacific Air", "PX055", time(8, 0), time(9, 20), 96, 11),
        RouteOption("Coastline Airways", "CL118", time(16, 35), time(17, 55), 112, 6),
    ),
    ("SFO", "JFK"): (
        RouteOption("Nimbus Air", "NB300", time(10, 15), time(18, 45), 332, 6),
        RouteOption("Pacific Air", "PX301", time(22, 0), time(6, 30), 298, 4),
    ),
    ("BOS", "MIA"): (
        RouteOption("Atlantic Link", "AL700", time(11, 0), time(14, 35), 233, 7),
        RouteOption("Nimbus Air", "NB712", time(19, 15), time(22, 50), 219, 5),
    ),
    ("ORD", "DEN"): (
        RouteOption("Midwest Wings", "MW615", time(13, 5), time(14, 50), 171, 10),
        RouteOption("Summit Air", "SA404", time(20, 25), time(22, 10), 149, 3),
    ),
    ("ATL", "LAS"): (
        RouteOption("Desert Star", "DS810", time(7, 10), time(9, 5), 244, 5),
        RouteOption("Atlantic Link", "AL811", time(15, 30), time(17, 25), 261, 4),
    ),
}


POLICIES: dict[str, str] = {
    "refund": (
        "Refundable fares can be refunded to the original form of payment until 24 hours before departure. "
        "Non-refundable fares receive airline credit minus any fare difference. Government taxes are always refundable."
    ),
    "change": (
        "Most tickets can be changed once without a service fee. The traveler pays any fare difference, and changes "
        "must be completed before the scheduled departure time."
    ),
    "baggage": (
        "One carry-on and one personal item are included. Checked bags can be added after booking, and fees depend "
        "on route and fare class."
    ),
    "support": "A customer support specialist can help with complex changes, accessibility needs, or payment issues.",
}
