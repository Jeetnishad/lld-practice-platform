"""
Seed script — populates the database with 5 LLD practice problems.
Run: python seed.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensions import db
from app.models import ProblemModel

PROBLEMS = [
    {
        "slug": "parking-lot",
        "title": "Parking Lot",
        "difficulty": "medium",
        "short_description": "Design a parking lot system that manages vehicle entry, exit, and payment.",
        "detailed_requirements": """Design a Parking Lot management system with the following requirements:

1. The parking lot has multiple floors, each with multiple parking spots.
2. Support different vehicle types: Motorcycle, Car, Truck/Bus.
3. Each vehicle type occupies a different size spot: Small (motorcycle), Medium (car), Large (truck).
4. On entry: assign the nearest available spot, generate a ticket with entry time.
5. On exit: calculate parking fee based on duration and vehicle type, mark spot as available.
6. Support multiple payment methods: Cash, Credit Card, UPI.
7. Track occupancy per floor and per spot type.
8. The system should handle the lot being full (no available spots).
9. Support reserved spots for disabled parking.
10. Admin can view real-time occupancy reports.""",
        "assumptions": """- Single parking lot with configurable floors and spots per floor.
- Pricing is flat-rate per hour (configurable per vehicle type).
- One vehicle per spot at a time.
- Tickets are identified by a unique ID.
- Payment is processed at a payment terminal, not in-lane.
- Spot assignment uses nearest-available (lowest floor, lowest spot number).""",
        "submission_guidance": """Your submission should include:
- Core classes: ParkingLot, Floor, ParkingSpot, Vehicle, Ticket, Payment
- Interfaces: PaymentProcessor, SpotAssignmentStrategy
- Key methods: enterVehicle(), exitVehicle(), assignSpot(), calculateFee(), processPayment()
- How you handle: lot full, different vehicle types, payment failures
- Design patterns you applied and why
- How to extend: adding EV charging spots, subscription plans""",
    },
    {
        "slug": "elevator-system",
        "title": "Elevator System",
        "difficulty": "hard",
        "short_description": "Design an elevator control system for a multi-floor building.",
        "detailed_requirements": """Design an Elevator Control System with the following requirements:

1. A building has N floors and M elevators.
2. Users press Up/Down buttons on each floor.
3. Inside the elevator, users press a destination floor button.
4. The dispatcher assigns the most efficient elevator to a floor request.
5. An elevator can be: IDLE, MOVING_UP, MOVING_DOWN, STOPPED.
6. Elevators stop to pick up passengers going in the same direction.
7. Support an emergency stop button inside each elevator.
8. Support maintenance mode: take a specific elevator out of service.
9. Display current floor and direction in each elevator.
10. The system should be configurable for different building sizes.""",
        "assumptions": """- Elevators travel at a constant speed (1 floor per time unit).
- No weight sensor simulation required for MVP.
- A floor request is a tuple: (floor_number, direction).
- Multiple passengers can board at the same stop.
- Dispatcher uses SCAN (elevator algorithm) or SSTF — your choice, justify it.""",
        "submission_guidance": """Your submission should include:
- Core classes: Building, Elevator, ElevatorController/Dispatcher, FloorRequest, Door
- Interfaces: DispatchStrategy (for swappable dispatch algorithms)
- Key methods: requestElevator(), moveToFloor(), openDoor(), closeDoor(), emergencyStop()
- State machine for elevator states (IDLE, MOVING_UP, MOVING_DOWN, STOPPED)
- How you would extend: VIP floors, freight elevators, energy saving mode""",
    },
    {
        "slug": "vending-machine",
        "title": "Vending Machine",
        "difficulty": "easy",
        "short_description": "Design a vending machine that dispenses products and handles payments.",
        "detailed_requirements": """Design a Vending Machine system with the following requirements:

1. The machine holds multiple products, each in a specific slot.
2. Each slot has a product type, price, and quantity.
3. A user selects a product (by slot code, e.g., A1, B3).
4. The machine accepts coins and notes (denominations: 1, 2, 5, 10, 20, 50, 100).
5. If inserted amount >= price: dispense product and return change.
6. If product is out of stock: show message, return inserted money.
7. If insufficient money: show required amount, allow user to insert more or cancel.
8. On cancel: return all inserted money.
9. Admin can restock products and collect cash from the machine.
10. Maintain an audit log of all transactions.""",
        "assumptions": """- No network connectivity (offline vending machine).
- Change is given using the machine's internal cash inventory.
- If exact change can't be made, do not dispense (return money with apology).
- One product selection per transaction.
- Admin access requires a special admin code.""",
        "submission_guidance": """Your submission should include:
- Core classes: VendingMachine, Slot, Product, Inventory, Transaction, CashRegister
- State machine: IDLE → PRODUCT_SELECTED → ACCEPTING_MONEY → DISPENSING → CHANGE_RETURNED → IDLE
- Interfaces: PaymentHandler, ChangeCalculator
- Key methods: selectProduct(), insertMoney(), dispenseProduct(), returnChange(), restock()
- How you handle: insufficient change, out of stock, overpayment""",
    },
    {
        "slug": "movie-ticket-booking",
        "title": "Movie Ticket Booking",
        "difficulty": "medium",
        "short_description": "Design a movie ticket booking system like BookMyShow.",
        "detailed_requirements": """Design a Movie Ticket Booking System with the following requirements:

1. Theaters have multiple screens; each screen shows one movie at a time.
2. Each show has a specific date, time, movie, screen, and available seats.
3. Seats are categorized: Standard, Premium, Recliner (different prices).
4. A user can search movies by city, title, or genre.
5. A user can view shows for a selected movie.
6. A user can select seats and make a booking.
7. Booking must handle concurrent seat selection (two users select the same seat).
8. On successful booking: generate a booking confirmation with unique ID.
9. A booking can be cancelled within the cancellation window (before show time - 2 hours).
10. Apply discount codes / offers at checkout.""",
        "assumptions": """- Single city scope for MVP.
- Payment processing is abstracted (assume success unless card declined).
- Seat lock expires after 10 minutes if payment not completed.
- Each user can book max 6 seats per transaction.
- Cancellation refund is 100% if >2 hours before show, 0% otherwise.""",
        "submission_guidance": """Your submission should include:
- Core classes: Movie, Theater, Screen, Show, Seat, Booking, User, Payment
- Concurrency handling strategy for seat selection (optimistic vs pessimistic locking — justify)
- Interfaces: PaymentGateway, NotificationService, DiscountStrategy
- Key methods: searchShows(), selectSeats(), confirmBooking(), cancelBooking()
- How you handle: concurrent seat booking, seat hold expiry, discount application""",
    },
    {
        "slug": "splitwise",
        "title": "Splitwise",
        "difficulty": "hard",
        "short_description": "Design a bill-splitting and expense management application.",
        "detailed_requirements": """Design a Splitwise-like expense sharing application with the following requirements:

1. Users can create Groups (e.g., \"Roommates\", \"Trip to Goa\").
2. A user can add an Expense to a group with: title, amount, paid_by, and split_type.
3. Support split types: Equal, Exact (each person's share), Percentage, Share-based.
4. The system calculates who owes what to whom.
5. Balances are simplified: if A owes B ₹100 and B owes A ₹60, net is A owes B ₹40.
6. Users can settle debts: record a payment between two users.
7. Show each user's balance summary: total owed, total owed by others.
8. Expense history per group and per user.
9. Support adding/removing group members.
10. Email notification when an expense is added (abstract the notification).""",
        "assumptions": """- Currency is uniform (no currency conversion).
- Balances are calculated in-memory from the expense ledger.
- No partial settlements within a single expense (settle at the user-pair level).
- Groups have at most 50 members for MVP.
- Floating point precision: round to 2 decimal places.""",
        "submission_guidance": """Your submission should include:
- Core classes: User, Group, Expense, Split, Balance, Settlement, Transaction
- Split strategy (Strategy pattern recommended): EqualSplit, ExactSplit, PercentageSplit
- Interfaces: NotificationService, SplitStrategy
- Key methods: addExpense(), settleDebt(), calculateBalances(), simplifyDebts()
- How you handle: simplification algorithm, floating point, group member removal with outstanding balances""",
    },
]


def seed():
    app = create_app()
    with app.app_context():
        existing = ProblemModel.query.count()
        if existing >= len(PROBLEMS):
            print(f"Database already has {existing} problems. Skipping seed.")
            return

        for p in PROBLEMS:
            exists = ProblemModel.query.filter_by(slug=p["slug"]).first()
            if not exists:
                problem = ProblemModel(**p)
                db.session.add(problem)
                print(f"  Added: {p['title']}")

        db.session.commit()
        print(f"\nDone! Seeded {len(PROBLEMS)} LLD problems successfully.")


if __name__ == "__main__":
    seed()
