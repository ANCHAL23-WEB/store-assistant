"""Seed a PostgreSQL retail-store assistant database with synthetic electronics data.

Install dependencies first:
    pip install Faker psycopg2-binary python-dotenv

Set DATABASE_URL in a .env file at the project root (or current directory), then run:
    python db/seed_data.py

This will WIPE existing categories/products/inventory/employees/stores and reseed
from scratch with a much larger, more varied catalog (Reliance Digital scale).
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

TOTAL_PRODUCTS = 5000

DEFAULT_IMAGE = "https://images.unsplash.com/photo-1560343090-f0409e92791a?w=600&h=400&fit=crop"

CATEGORY_IMAGES = {
    "Mobile Phones": "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=600&h=400&fit=crop",
    "Laptops": "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=600&h=400&fit=crop",
    "Tablets": "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?w=600&h=400&fit=crop",
    "TVs": "https://images.unsplash.com/photo-1593359677879-a4bb92f829d1?w=600&h=400&fit=crop",
    "Refrigerators": "https://images.unsplash.com/photo-1571175443880-49e1d25b2bc5?w=600&h=400&fit=crop",
    "Washing Machines": "https://images.unsplash.com/photo-1626806787461-102c1bfaaea1?w=600&h=400&fit=crop",
    "Air Conditioners": "https://images.unsplash.com/photo-1631545806609-91ac6f6a48e5?w=600&h=400&fit=crop",
    "Kitchen Appliances": "https://images.unsplash.com/photo-1585659722983-3a675dabf23d?w=600&h=400&fit=crop",
    "Mixer Grinders": "https://images.unsplash.com/photo-1570222094114-d054a817e56b?w=600&h=400&fit=crop",
    "Small Appliances": "https://images.unsplash.com/photo-1522338242992-e1a54906a8da?w=600&h=400&fit=crop",
    "Vacuum Cleaners": "https://images.unsplash.com/photo-1558317374-067fb5f30001?w=600&h=400&fit=crop",
    "Headphones & Earbuds": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600&h=400&fit=crop",
    "Bluetooth Speakers": "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=600&h=400&fit=crop",
    "Soundbars": "https://images.unsplash.com/photo-1545454675-3531b543be5d?w=600&h=400&fit=crop",
    "Smartwatches": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600&h=400&fit=crop",
    "Cameras": "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?w=600&h=400&fit=crop",
    "Gaming Consoles & Accessories": "https://images.unsplash.com/photo-1486401899868-0e435ed85128?w=600&h=400&fit=crop",
}

CATEGORY_DETAILS = {
    "Mobile Phones": {
        "brands": ["Samsung", "Apple", "Xiaomi", "OnePlus", "Realme", "Vivo", "Oppo", "Google"],
        "models": ["Smartphone", "5G Smartphone"],
        "price_range": (8000, 150000),
        "specs": lambda: {
            "ram_gb": random.choice([4, 6, 8, 12, 16]),
            "storage_gb": random.choice([64, 128, 256, 512]),
            "battery_mah": random.choice([4000, 4500, 5000, 5500]),
            "camera_mp": random.choice([12, 48, 50, 64, 108, 200]),
            "five_g": random.choice([True, False]),
            "fingerprint_sensor": True,
        },
    },
    "Laptops": {
        "brands": ["HP", "Dell", "Lenovo", "Asus", "Acer", "Apple", "MSI"],
        "models": ["Laptop", "Gaming Laptop", "Ultrabook"],
        "price_range": (28000, 220000),
        "specs": lambda: {
            "ram_gb": random.choice([8, 16, 32, 64]),
            "storage_gb": random.choice([256, 512, 1024]),
            "processor": random.choice(["Intel i5", "Intel i7", "Intel i9", "AMD Ryzen 5", "AMD Ryzen 7", "Apple M2"]),
            "screen_size_inches": random.choice([13, 14, 15, 16, 17]),
            "touchscreen": random.choice([True, False]),
        },
    },
    "Tablets": {
        "brands": ["Apple", "Samsung", "Lenovo", "Xiaomi", "Realme"],
        "models": ["Tablet"],
        "price_range": (9000, 90000),
        "specs": lambda: {
            "ram_gb": random.choice([4, 6, 8, 12]),
            "storage_gb": random.choice([64, 128, 256]),
            "screen_size_inches": random.choice([8, 10, 11, 12]),
            "cellular_sim_support": random.choice([True, False]),
            "stylus_support": random.choice([True, False]),
        },
    },
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
            "smart_features": random.choice([[], ["WiFi"], ["WiFi", "App Control"]]),
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
            "smart_features": random.choice([[], ["WiFi"], ["WiFi", "App Control"]]),
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
            "smart_features": random.choice([[], ["WiFi"], ["WiFi", "App Control"]]),
            "energy_rating": random.choice(["3 Star", "4 Star", "5 Star"]),
        },
    },
    "Kitchen Appliances": {
        "brands": ["Philips", "Prestige", "Bajaj", "Havells", "Elica", "Faber", "Morphy Richards"],
        "models": ["Microwave Oven", "Kitchen Chimney", "Induction Cooktop", "Electric Kettle"],
        "price_range": (1800, 35000),
        "specs": lambda: {
            "appliance_type": random.choice(["Microwave", "Chimney", "Induction", "Kettle"]),
            "power_watts": random.choice([500, 750, 1000, 1200, 1500, 2000]),
            "sensor_based": random.choice([True, False]),
            "auto_clean": random.choice([True, False]),
            "warranty_years": random.choice([1, 2, 3]),
        },
    },
    "Mixer Grinders": {
        "brands": ["Prestige", "Bajaj", "Philips", "Butterfly", "Preethi"],
        "models": ["Mixer Grinder"],
        "price_range": (1800, 12000),
        "specs": lambda: {
            "jars": random.choice([2, 3, 4]),
            "power_watts": random.choice([500, 550, 750, 1000]),
            "warranty_years": random.choice([1, 2, 5]),
        },
    },
    "Small Appliances": {
        "brands": ["Philips", "Havells", "Panasonic", "Syska", "Nova"],
        "models": ["Hair Dryer", "Trimmer", "Iron"],
        "price_range": (500, 6000),
        "specs": lambda: {
            "appliance_type": random.choice(["Hair Dryer", "Trimmer", "Iron"]),
            "power_watts": random.choice([1000, 1200, 1500, 1800]),
            "cordless": random.choice([True, False]),
        },
    },
    "Vacuum Cleaners": {
        "brands": ["Eureka Forbes", "Dyson", "Philips", "Kent", "Xiaomi"],
        "models": ["Robot Vacuum Cleaner", "Handheld Vacuum Cleaner", "Canister Vacuum Cleaner"],
        "price_range": (3000, 45000),
        "specs": lambda: {
            "vacuum_type": random.choice(["Robot", "Handheld", "Canister"]),
            "suction_power_watts": random.choice([300, 500, 800, 1200]),
            "bagless": random.choice([True, False]),
            "smart_features": random.choice([[], ["WiFi"], ["WiFi", "App Control"]]),
        },
    },
    "Headphones & Earbuds": {
        "brands": ["boAt", "JBL", "Sony", "Apple", "Samsung", "Noise"],
        "models": ["True Wireless Earbuds", "Over-Ear Headphones", "In-Ear Headphones"],
        "price_range": (600, 35000),
        "specs": lambda: {
            "type": random.choice(["True Wireless", "Over-Ear", "In-Ear"]),
            "battery_life_hours": random.choice([6, 10, 20, 30, 40]),
            "noise_cancellation": random.choice([True, False]),
            "bluetooth": True,
        },
    },
    "Bluetooth Speakers": {
        "brands": ["JBL", "boAt", "Sony", "Marshall", "Zebronics"],
        "models": ["Bluetooth Speaker", "Portable Speaker"],
        "price_range": (800, 25000),
        "specs": lambda: {
            "battery_life_hours": random.choice([4, 8, 12, 20]),
            "waterproof": random.choice([True, False]),
            "power_watts": random.choice([5, 10, 20, 30, 50]),
        },
    },
    "Soundbars": {
        "brands": ["Sony", "JBL", "boAt", "Samsung", "Zebronics"],
        "models": ["Soundbar"],
        "price_range": (2500, 55000),
        "specs": lambda: {
            "channels": random.choice(["2.0", "2.1", "3.1", "5.1"]),
            "power_watts": random.choice([40, 80, 120, 200]),
            "wireless_subwoofer": random.choice([True, False]),
        },
    },
    "Smartwatches": {
        "brands": ["Apple", "Samsung", "Noise", "boAt", "Fire-Boltt", "Titan"],
        "models": ["Smartwatch"],
        "price_range": (1500, 55000),
        "specs": lambda: {
            "display_type": random.choice(["AMOLED", "LCD"]),
            "battery_life_days": random.choice([1, 2, 5, 7, 14]),
            "gps": random.choice([True, False]),
            "calling_support": random.choice([True, False]),
        },
    },
    "Cameras": {
        "brands": ["Canon", "Nikon", "Sony", "Fujifilm", "GoPro"],
        "models": ["DSLR Camera", "Mirrorless Camera", "Action Camera"],
        "price_range": (8000, 250000),
        "specs": lambda: {
            "camera_type": random.choice(["DSLR", "Mirrorless", "Action"]),
            "megapixels": random.choice([16, 20, 24, 32, 45]),
            "video_resolution": random.choice(["1080p", "4K"]),
            "image_stabilization": random.choice([True, False]),
        },
    },
    "Gaming Consoles & Accessories": {
        "brands": ["Sony", "Microsoft", "Nintendo", "Logitech", "Razer"],
        "models": ["Gaming Console", "Gaming Controller", "Gaming Headset"],
        "price_range": (2000, 60000),
        "specs": lambda: {
            "product_type": random.choice(["Console", "Controller", "Headset"]),
            "storage_gb": random.choice([None, 512, 1000, 2000]),
            "wireless": random.choice([True, False]),
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
    """Build product rows distributed across all categories, totalling ~TOTAL_PRODUCTS."""
    rows = []
    category_names = list(CATEGORY_DETAILS.keys())
    base_count = TOTAL_PRODUCTS // len(category_names)
    remainder = TOTAL_PRODUCTS - (base_count * len(category_names))

    for position, category_name in enumerate(category_names):
        details = CATEGORY_DETAILS[category_name]
        count = base_count + (1 if position < remainder else 0)
        image_url = CATEGORY_IMAGES.get(category_name, DEFAULT_IMAGE)
        for _ in range(count):
            brand = random.choice(details["brands"])
            model = random.choice(details["models"])
            low, high = details["price_range"]
            price = Decimal(random.randint(low, high - 1)) + Decimal("0.00")
            product_name = f"{brand} {model} {faker.bothify(text='??-###').upper()}"
            barcode = "890" + str(random.randint(10**9, 10**10 - 1))
            rows.append((
                product_name,
                category_ids[category_name],
                brand,
                price,
                random.sample(COLORS, k=random.randint(1, 3)),
                Json(details["specs"]()),
                image_url,
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
            # Wipe existing data so the catalog is rebuilt cleanly (a backup was taken first).
            cursor.execute(
                "TRUNCATE TABLE usage_events, price_match_events, inventory, products, "
                "employees, categories, stores RESTART IDENTITY CASCADE"
            )

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

    print(f"Seeded {len(CATEGORY_DETAILS)} categories, {len(product_ids)} products, "
          f"{len(STORES)} stores, {len(inventory_rows)} inventory rows, and 20 employees.")


if __name__ == "__main__":
    main()