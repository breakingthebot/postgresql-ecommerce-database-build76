"""
Deterministic synthetic data generator and database seeder.
Populates all 12 relational tables with realistic, constraint-compliant data.
"""

from __future__ import annotations

import datetime
import json
import random
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pg_ecommerce.db import DatabaseConnection


class DataSeeder:
    """High-performance deterministic data generation and database population."""

    CATEGORIES_TREE = [
        {"id": 1, "parent_id": None, "name": "Electronics", "slug": "electronics", "path": "/electronics", "depth": 0},
        {"id": 2, "parent_id": 1, "name": "Audio & Sound", "slug": "audio-sound", "path": "/electronics/audio-sound", "depth": 1},
        {"id": 3, "parent_id": 2, "name": "Noise-Cancelling", "slug": "noise-cancelling", "path": "/electronics/audio-sound/noise-cancelling", "depth": 2},
        {"id": 4, "parent_id": 1, "name": "Computers & Peripherals", "slug": "computers-peripherals", "path": "/electronics/computers-peripherals", "depth": 1},
        {"id": 5, "parent_id": None, "name": "Apparel & Activewear", "slug": "apparel-activewear", "path": "/apparel-activewear", "depth": 0},
        {"id": 6, "parent_id": 5, "name": "Outerwear & Jackets", "slug": "outerwear-jackets", "path": "/apparel-activewear/outerwear-jackets", "depth": 1},
        {"id": 7, "parent_id": None, "name": "Home & Smart Living", "slug": "home-smart-living", "path": "/home-smart-living", "depth": 0},
        {"id": 8, "parent_id": 7, "name": "Smart Lighting", "slug": "smart-lighting", "path": "/home-smart-living/smart-lighting", "depth": 1},
    ]

    BRAND_CATALOG = [
        {"id": 1, "name": "Apex Audio", "slug": "apex-audio", "website": "https://apexaudio.example.com", "country": "US"},
        {"id": 2, "name": "Volt Electronics", "slug": "volt-electronics", "website": "https://voltelectronics.example.com", "country": "JP"},
        {"id": 3, "name": "Nordic Gear", "slug": "nordic-gear", "website": "https://nordicgear.example.com", "country": "SE"},
        {"id": 4, "name": "Terra Outdoor", "slug": "terra-outdoor", "website": "https://terraoutdoor.example.com", "country": "DE"},
        {"id": 5, "name": "Lumina Systems", "slug": "lumina-systems", "website": "https://luminasystems.example.com", "country": "US"},
        {"id": 6, "name": "Pulse Tech", "slug": "pulse-tech", "website": "https://pulsetech.example.com", "country": "KR"},
        {"id": 7, "name": "Aero Carbon", "slug": "aero-carbon", "website": "https://aerocarbon.example.com", "country": "TW"},
        {"id": 8, "name": "Solstice Apparel", "slug": "solstice-apparel", "website": "https://solsticeapparel.example.com", "country": "CA"},
    ]

    PRODUCT_TEMPLATES = [
        ("Studio ANC Headphones", 249.99, ["audio", "anc", "headphones", "bluetooth"], {"drivers": "40mm", "anc_db": 42}),
        ("Wireless Sport Earbuds", 129.99, ["audio", "earbuds", "fitness", "waterproof"], {"rating": "IPX7", "battery_hours": 32}),
        ("Mechanical Ergonomic Keyboard", 179.50, ["peripherals", "keyboard", "gaming", "rgb"], {"switches": "Gateron Brown", "hot_swap": True}),
        ("Ultra-Light Gaming Mouse", 79.99, ["peripherals", "mouse", "gaming", "sensor"], {"dpi": 26000, "weight_g": 58}),
        ("Expedition Down Parka", 399.00, ["apparel", "winter", "waterproof", "down"], {"fill_power": 850, "temp_c": -30}),
        ("Thermal Base Layer Top", 65.00, ["apparel", "merino", "thermal", "active"], {"material": "100% Merino Wool", "weight_gsm": 200}),
        ("Circadian Desk Lamp", 119.00, ["lighting", "home", "smart", "desk"], {"lumens": 950, "cri": 98}),
        ("Smart RGB Lightstrip Pro", 49.99, ["lighting", "home", "rgb", "ambient"], {"length_m": 5, "protocol": "Matter/Thread"}),
        ("Thunderbolt 4 Docking Station", 289.00, ["peripherals", "dock", "thunderbolt", "usb-c"], {"power_delivery_w": 100, "display_support": "8K"}),
        ("Active Carbon Water Filter", 35.00, ["home", "water", "filter", "kitchen"], {"gallons": 1000, "stages": 4}),
    ]

    COLORS = ["Midnight Black", "Arctic White", "Space Gray", "Navy Blue", "Forest Green", "Sunset Orange"]
    SIZES = ["XS", "S", "M", "L", "XL", "XXL"]
    FIRST_NAMES = ["Liam", "Olivia", "Noah", "Emma", "Oliver", "Charlotte", "Elijah", "Amelia", "James", "Sophia", "Lucas", "Mia", "Alexander", "Isabella", "Benjamin", "Ava"]
    LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson"]
    CITIES = [
        ("San Francisco", "CA", "94105"),
        ("Seattle", "WA", "98101"),
        ("New York", "NY", "10001"),
        ("Austin", "TX", "78701"),
        ("Chicago", "IL", "60601"),
        ("Denver", "CO", "80202"),
        ("Boston", "MA", "02110"),
    ]

    def __init__(self, db: DatabaseConnection, seed: int = 42):
        self.db = db
        self.rng = random.Random(seed)

    def apply_curated_seed(self, sql_file: Optional[Path] = None) -> None:
        """Apply curated seed data from SQL script."""
        if not sql_file:
            pkg_dir = Path(__file__).parent.parent.parent
            sql_file = pkg_dir / "sql" / "02_seed_data.sql"

        content = sql_file.read_text(encoding="utf-8")
        self.db.execute(content)

    def generate_synthetic_dataset(
        self,
        num_products: int = 50,
        num_customers: int = 30,
        num_orders: int = 60,
    ) -> Dict[str, int]:
        """
        Generate and insert large synthetic datasets deterministically.
        Strictly satisfies all relational constraints, cascades, and checks.
        """
        # 1. Seed Brands & Categories
        for brand in self.BRAND_CATALOG:
            self.db.execute(
                """
                INSERT INTO brands (id, name, slug, website, country)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT (id) DO NOTHING;
                """,
                (brand["id"], brand["name"], brand["slug"], brand["website"], brand["country"]),
            )

        for cat in self.CATEGORIES_TREE:
            self.db.execute(
                """
                INSERT INTO categories (id, parent_id, name, slug, hierarchy_path, depth, is_active)
                VALUES (?, ?, ?, ?, ?, ?, 1)
                ON CONFLICT (id) DO NOTHING;
                """,
                (cat["id"], cat["parent_id"], cat["name"], cat["slug"], cat["path"], cat["depth"]),
            )

        # 2. Seed Products, Variants, and Inventory
        variant_records: List[Dict[str, Any]] = []
        variant_counter = 1

        for p_idx in range(1, num_products + 1):
            tmpl_name, base_price, tags, metadata = self.rng.choice(self.PRODUCT_TEMPLATES)
            brand_id = self.rng.choice(self.BRAND_CATALOG)["id"]
            category_id = self.rng.choice(self.CATEGORIES_TREE)["id"]
            name = f"{tmpl_name} Model-{p_idx:03d}"
            slug = f"{name.lower().replace(' ', '-').replace('/', '-')}-{p_idx}"

            self.db.execute(
                """
                INSERT INTO products (id, brand_id, category_id, name, slug, description, base_price, status, is_featured, tags, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?)
                ON CONFLICT (id) DO NOTHING;
                """,
                (
                    p_idx,
                    brand_id,
                    category_id,
                    name,
                    slug,
                    f"High performance {name} engineered for reliability and sleek modern aesthetics.",
                    base_price,
                    1 if self.rng.random() > 0.8 else 0,
                    json.dumps(tags),
                    json.dumps(metadata),
                ),
            )

            # Generate 1 to 3 variants per product
            num_variants = self.rng.randint(1, 3)
            for v_idx in range(num_variants):
                color = self.rng.choice(self.COLORS)
                size = self.rng.choice(self.SIZES)
                sku = f"SKU-{p_idx:04d}-{color[:3].upper()}-{v_idx}"
                barcode = f"84000{p_idx:04d}{v_idx:02d}"
                attrs = {"color": color, "size": size}
                price_override = base_price if v_idx == 0 else round(base_price * self.rng.uniform(0.95, 1.15), 2)
                weight = self.rng.randint(100, 2500)

                self.db.execute(
                    """
                    INSERT INTO product_variants (id, product_id, sku, barcode, attributes, price_override, weight_grams, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                    ON CONFLICT (id) DO NOTHING;
                    """,
                    (variant_counter, p_idx, sku, barcode, json.dumps(attrs), price_override, weight),
                )

                # Inventory: satisfy chk_inventory_reserved_lte_hand
                qty_hand = self.rng.randint(20, 200)
                qty_reserved = self.rng.randint(0, min(qty_hand, 25))
                self.db.execute(
                    """
                    INSERT INTO inventory (variant_id, warehouse_code, quantity_on_hand, quantity_reserved, reorder_point)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT (variant_id) DO UPDATE SET
                        quantity_on_hand = excluded.quantity_on_hand,
                        quantity_reserved = excluded.quantity_reserved;
                    """,
                    (variant_counter, self.rng.choice(["WH-CENTRAL", "WH-WEST", "WH-EAST"]), qty_hand, qty_reserved, 15),
                )

                variant_records.append({
                    "id": variant_counter,
                    "product_id": p_idx,
                    "product_name": name,
                    "sku": sku,
                    "price": price_override,
                })
                variant_counter += 1

        # 3. Seed Customers & Addresses
        customer_ids: List[str] = []
        for c_idx in range(1, num_customers + 1):
            cid = str(uuid.UUID(int=c_idx + 1000000))
            fn = self.rng.choice(self.FIRST_NAMES)
            ln = self.rng.choice(self.LAST_NAMES)
            email = f"{fn.lower()}.{ln.lower()}{c_idx}@example.com"
            self.db.execute(
                """
                INSERT INTO customers (id, email, full_name, role, is_active, metadata)
                VALUES (?, ?, ?, 'customer', 1, ?)
                ON CONFLICT (id) DO NOTHING;
                """,
                (cid, email, f"{fn} {ln}", json.dumps({"loyalty_points": self.rng.randint(0, 500)})),
            )
            customer_ids.append(cid)

            # Insert default address
            city, state, zipcode = self.rng.choice(self.CITIES)
            aid = str(uuid.UUID(int=c_idx + 2000000))
            self.db.execute(
                """
                INSERT INTO addresses (id, customer_id, type, recipient_name, street_line1, city, state, postal_code, country, is_default)
                VALUES (?, ?, 'both', ?, ?, ?, ?, ?, 'US', 1)
                ON CONFLICT (id) DO NOTHING;
                """,
                (aid, cid, f"{fn} {ln}", f"{self.rng.randint(100, 9999)} Commerce Way", city, state, zipcode),
            )

        # 4. Seed Coupons
        coupons = [
            (1, "SAVE10", "percentage", 10.00, 50.00),
            (2, "FLAT25", "fixed", 25.00, 150.00),
            (3, "FLASH50", "fixed", 50.00, 300.00),
        ]
        now = datetime.datetime.now(datetime.timezone.utc)
        valid_from = (now - datetime.timedelta(days=30)).isoformat()
        valid_until = (now + datetime.timedelta(days=90)).isoformat()

        for cpid, code, dtype, val, min_val in coupons:
            self.db.execute(
                """
                INSERT INTO coupons (id, code, discount_type, discount_value, min_order_value, max_uses, uses_count, valid_from, valid_until, is_active)
                VALUES (?, ?, ?, ?, ?, 1000, 15, ?, ?, 1)
                ON CONFLICT (id) DO NOTHING;
                """,
                (cpid, code, dtype, val, min_val, valid_from, valid_until),
            )

        # 5. Seed Orders and Line Items
        order_item_counter = 1
        for o_idx in range(1, num_orders + 1):
            oid = str(uuid.UUID(int=o_idx + 3000000))
            cid = self.rng.choice(customer_ids)
            order_num = f"ORD-2026-{10000 + o_idx}"
            status = self.rng.choice(["delivered", "shipped", "paid", "processing", "pending"])

            # Pick 1-4 random variants for order items
            items_to_buy = self.rng.sample(variant_records, k=self.rng.randint(1, min(4, len(variant_records))))
            subtotal = 0.0
            order_items_payload = []

            for item in items_to_buy:
                qty = self.rng.randint(1, 3)
                unit_price = float(item["price"])
                line_total = round(unit_price * qty, 2)
                subtotal += line_total
                order_items_payload.append((order_item_counter, oid, item["id"], item["product_name"], item["sku"], unit_price, qty, line_total))
                order_item_counter += 1

            subtotal = round(subtotal, 2)
            coupon_id = 1 if (self.rng.random() > 0.6 and subtotal >= 50) else None
            discount = round(subtotal * 0.10, 2) if coupon_id else 0.00
            tax = round((subtotal - discount) * 0.08, 2)
            shipping = 0.00 if subtotal > 150 else 15.00
            total_amount = round(subtotal - discount + tax + shipping, 2)

            city, state, zipc = self.rng.choice(self.CITIES)
            addr_json = json.dumps({"street": "100 Delivery St", "city": city, "state": state, "zip": zipc})

            days_ago = self.rng.randint(1, 90)
            placed_at = (now - datetime.timedelta(days=days_ago)).isoformat()

            self.db.execute(
                """
                INSERT INTO orders (id, customer_id, coupon_id, order_number, status, subtotal, discount_amount, tax_amount, shipping_fee, total_amount, shipping_address, billing_address, payment_method, placed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'credit_card', ?)
                ON CONFLICT (id) DO NOTHING;
                """,
                (oid, cid, coupon_id, order_num, status, subtotal, discount, tax, shipping, total_amount, addr_json, addr_json, placed_at),
            )

            # Insert line items
            for item_row in order_items_payload:
                self.db.execute(
                    """
                    INSERT INTO order_items (id, order_id, variant_id, product_name_snapshot, sku_snapshot, unit_price, quantity, line_total)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT (id) DO NOTHING;
                    """,
                    item_row,
                )

            # Insert order status transition
            self.db.execute(
                """
                INSERT INTO order_status_history (order_id, from_status, to_status, change_reason, changed_by, changed_at)
                VALUES (?, NULL, ?, 'Order placed by customer', 'checkout_engine', ?);
                """,
                (oid, status, placed_at),
            )

        # 6. Seed Reviews (Unique product_id, customer_id pairs)
        review_counter = 1
        for p_idx in range(1, num_products + 1):
            reviewers = self.rng.sample(customer_ids, k=self.rng.randint(1, min(5, len(customer_ids))))
            for cid in reviewers:
                rating = self.rng.choices([5, 4, 3, 2, 1], weights=[50, 30, 10, 5, 5])[0]
                self.db.execute(
                    """
                    INSERT INTO reviews (id, product_id, customer_id, rating, title, body, is_verified_purchase, helpful_votes)
                    VALUES (?, ?, ?, ?, ?, ?, 1, ?)
                    ON CONFLICT (product_id, customer_id) DO NOTHING;
                    """,
                    (
                        review_counter,
                        p_idx,
                        cid,
                        rating,
                        f"Great product - {rating} stars!",
                        "Exceeded expectations in build quality, performance, and day-to-day durability.",
                        self.rng.randint(0, 50),
                    ),
                )
                review_counter += 1

        return self.get_table_counts()

    def get_table_counts(self) -> Dict[str, int]:
        """Return total row counts for all 12 core tables."""
        tables = [
            "brands", "categories", "customers", "addresses", "products",
            "product_variants", "inventory", "coupons", "orders",
            "order_items", "order_status_history", "reviews"
        ]
        counts: Dict[str, int] = {}
        for tbl in tables:
            res = self.db.fetch_one(f"SELECT COUNT(*) AS count FROM {tbl};")
            counts[tbl] = res["count"] if res else 0
        return counts
