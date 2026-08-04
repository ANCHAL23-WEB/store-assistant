"""Seed a PostgreSQL retail-store assistant database with synthetic electronics data.

Install dependencies first:
    pip install Faker psycopg2-binary python-dotenv

Set DATABASE_URL in a .env file at the project root (or current directory), then run:
    python db/seed_data.py
"""
import os
import random
from decimal import Decimal
from pathlib import Path

import psycopg2
from dotenv import load_dotenv
from faker import Faker
from psycopg2.extras import Json, execute_values

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

faker = Faker("en_IN")

CATEGORY_DETAILS = {
    "TVs": {
        "brands": ["Samsung", "LG", "Sony", "TCL", "Hisense", "Xiaomi"],
        "models": ["4K Smart TV", "QLED TV", "OLED TV", "LED Smart TV"],
        "price_range": (22000, 220000),
        "specs": lambda: {
            "screen_size_inches": random.choice([32, 43, 50, 55, 65, 75]),
            "resolution": random.choice(["Full HD", "4K UHD", "8K UHD"]),
            "panel": random.choice(["LED", "QLED", "OLED"]),
            "smart_tv": True,
            "energy_rating": random.choice(["3 Star", "4 Star", "5 Star"]),
        },
    },
    "Refrigerators": {
        "brands": ["LG", "Samsung", "Whirlpool", "Godrej", "Haier", "Bosch"],
        "models": ["Double Door Refrigerator", "Single Door Refrigerator", "Side-by-Side Refrigerator"],
        "price_range": (18000, 145000),
        "specs": lambda: {
            "capacity_litres": random.choice([190, 236, 260, 340, 420, 580]),
            "door_type": random.choice(["Single Door", "Double Door", "Side-by-Side"]),
            "compressor": "Inverter",
            "energy_rating": random.choice(["2 Star", "3 Star", "4 Star", "5 Star"]),
        },
    },
    "Washing Machines": {
        "brands": ["LG", "Samsung", "IFB", "Bosch", "Whirlpool", "Haier"],
        "models": ["Front Load Washing Machine", "Top Load Washing Machine", "Semi-Automatic Washing Machine"],
        "price_range": (9000, 70000),
        "specs": lambda: {
            "capacity_kg": random.choice([6, 6.5, 7, 7.5, 8, 9, 10]),
            "load_type": random.choice(["Front Load", "Top Load", "Semi-Automatic"]),
            "spin_speed_rpm": random.choice([1000, 1200, 1400]),
            "energy_rating": random.choice(["3 Star", "4 Star", "5 Star"]),
        },
    },
    "Air Conditioners": {
        "brands": ["Daikin", "LG", "Samsung", "Voltas", "Blue Star", "Carrier"],
        "models": ["Split Inverter AC", "Window AC", "Hot and Cold AC"],
        "price_range": (28000, 105000),
        "specs": lambda: {
            "tonnage": random.choice([1, 1.2, 1.5, 1.8, 2]),
            "ac_type": random.choice(["Split", "Window"]),
            "inverter": True,
            "energy_rating": random.choice(["3 Star", "4 Star", "5 Star"]),
        },
    },
    "Kitchen Appliances": {
        "brands": ["Philips", "Prestige", "Bajaj", "Havells", "Usha", "Morphy Richards"],
        "models": ["Mixer Grinder", "Microwave Oven", "Air Fryer", "Induction Cooktop", "Electric Kettle"],
        "price_range": (1800, 30000),
        "specs": lambda: {
            "appliance_type": random.choice(["Mixer", "Microwave", "Air Fryer", "Induction", "Kettle"]),
            "power_watts": random.choice([500, 750, 1000, 1200, 1500, 2000]),
            "warranty_years": random.choice([1, 2, 3]),
            "energy_rating": random.choice(["3 Star", "4 Star", "5 Star"]),
        },
    },
}

STORES = [
    ("TechHub Indiranagar", "100 Feet Road, Indiranagar", "Bengaluru"),
    ("TechHub Andheri", "Linking Road, Andheri West", "Mumbai"),
    ("TechHub Saket", "Select Citywalk, Saket", "New Delhi"),
    ("TechHub T. Nagar", "Usman Road, T. Nagar", "Chennai"),
    ("TechHub Salt Lake", "Sector V, Salt Lake", "Kolkata"),
]

COLORS = ["Black", "White", "Silver", "Grey", "Blue", "Red"]


def product_rows(category_ids: dict[str, int]) -> list[tuple]:
    """Build 1,000 product rows distributed evenly across the five categories."""
    rows = []
    for category_name, details in CATEGORY_DETAILS.items():
        for index in range(200):
            brand = random.choice(details["brands"])
            model = random.choice(details["models"])
            low, high = details["price_range"]
            price = Decimal(random.randint(low, high - 1)) + Decimal("0.00")
            product_name = f"{brand} {model} {faker.bothify(text='??-###').upper()}"
            image_slug = product_name.lower().replace(" ", "-")
            barcode = "890" + str(random.randint(10**9, 10**10 - 1))
            rows.append((
                product_name,
                category_ids[category_name],
                brand,
                price,
                random.sample(COLORS, k=random.randint(1, 3)),
                Json(details["specs"]()),
                f"https://placehold.co/600x400?text={image_slug}",
                barcode,
            ))
    random.shuffle(rows)
    return rows


def main() -> None:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is missing. Add it to the project's .env file.")

    with psycopg2.connect(database_url) as connection:
        with connection.cursor() as cursor:
            # Insert category and store records, retaining generated IDs for relations.
            category_ids = {}
            for name in CATEGORY_DETAILS:
                cursor.execute(
                    "INSERT INTO categories (name) VALUES (%s) RETURNING category_id", (name,)
                )
                category_ids[name] = cursor.fetchone()[0]

            store_results = execute_values(
                cursor,
                "INSERT INTO stores (name, location, city) VALUES %s RETURNING store_id",
                STORES,
                fetch=True,
            )
            store_ids = [row[0] for row in store_results]

            # Batch insertion keeps the script quick while still returning product IDs.
            product_results = execute_values(
                cursor,
                """
                INSERT INTO products
                    (name, category_id, brand, price, colors, specs, image_url, barcode)
                VALUES %s
                RETURNING product_id
                """,
                product_rows(category_ids),
                page_size=200,
                fetch=True,
            )
            product_ids = [row[0] for row in product_results]

            inventory_rows = [
                (product_id, store_id, random.randint(0, 40), random.choice([None, 2, 3, 5, 7]))
                for product_id in product_ids
                for store_id in store_ids
            ]
            execute_values(
                cursor,
                """
                INSERT INTO inventory (product_id, store_id, stock_qty, restock_eta_days)
                VALUES %s
                """,
                inventory_rows,
                page_size=500,
            )

            employee_rows = [
                (faker.name(), store_ids[index % len(store_ids)], "admin" if index < 5 else "staff")
                for index in range(20)
            ]
            execute_values(
                cursor,
                "INSERT INTO employees (name, store_id, role) VALUES %s",
                employee_rows,
            )

        # The context manager commits on successful completion.
    print("Seeded 5 categories, 1,000 products, 5 stores, 5,000 inventory rows, and 20 employees.")


if __name__ == "__main__":
    main()