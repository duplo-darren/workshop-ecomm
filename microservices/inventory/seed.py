"""Seed the inventory database with sample stock levels."""
from .app import create_app
from .models import db, Inventory

STOCK = [
    # Electronics
    {"product_id": 1,  "quantity": 50,  "warehouse": "main"},  # Wireless Headphones
    {"product_id": 2,  "quantity": 30,  "warehouse": "main"},  # Mechanical Keyboard
    {"product_id": 3,  "quantity": 100, "warehouse": "main"},  # USB-C Hub
    {"product_id": 4,  "quantity": 75,  "warehouse": "main"},  # Laptop Stand
    {"product_id": 5,  "quantity": 45,  "warehouse": "main"},  # Webcam HD
    {"product_id": 6,  "quantity": 40,  "warehouse": "main"},  # Smart Watch
    {"product_id": 7,  "quantity": 60,  "warehouse": "main"},  # Portable Bluetooth Speaker
    {"product_id": 8,  "quantity": 55,  "warehouse": "main"},  # Noise-Cancelling Earbuds
    {"product_id": 9,  "quantity": 25,  "warehouse": "main"},  # 4K Action Camera
    {"product_id": 10, "quantity": 70,  "warehouse": "main"},  # Smart Home Hub
    {"product_id": 11, "quantity": 90,  "warehouse": "main"},  # Wireless Charging Pad
    {"product_id": 12, "quantity": 35,  "warehouse": "main"},  # E-Reader
    {"product_id": 13, "quantity": 80,  "warehouse": "main"},  # Portable Power Bank
    {"product_id": 14, "quantity": 65,  "warehouse": "main"},  # LED Desk Lamp
    {"product_id": 15, "quantity": 30,  "warehouse": "main"},  # Digital Photo Frame
    # Home & Kitchen
    {"product_id": 16, "quantity": 120, "warehouse": "main"},  # Stainless Steel Water Bottle
    {"product_id": 17, "quantity": 45,  "warehouse": "main"},  # Coffee Grinder
    {"product_id": 18, "quantity": 30,  "warehouse": "main"},  # Air Purifier
    {"product_id": 19, "quantity": 85,  "warehouse": "main"},  # Bamboo Cutting Board
    {"product_id": 20, "quantity": 50,  "warehouse": "main"},  # Cast Iron Skillet
    {"product_id": 21, "quantity": 40,  "warehouse": "main"},  # Instant Pot
    {"product_id": 22, "quantity": 20,  "warehouse": "main"},  # Sous Vide Precision Cooker
    {"product_id": 23, "quantity": 35,  "warehouse": "main"},  # Handheld Vacuum
    # Sports & Outdoors
    {"product_id": 24, "quantity": 110, "warehouse": "main"},  # Resistance Bands Set
    {"product_id": 25, "quantity": 95,  "warehouse": "main"},  # Yoga Mat
    {"product_id": 26, "quantity": 150, "warehouse": "main"},  # Jump Rope
    {"product_id": 27, "quantity": 75,  "warehouse": "main"},  # Foam Roller
    {"product_id": 28, "quantity": 40,  "warehouse": "main"},  # Hiking Backpack
    {"product_id": 29, "quantity": 30,  "warehouse": "main"},  # Trekking Poles
    {"product_id": 30, "quantity": 55,  "warehouse": "main"},  # Hydration Pack
    # Books & Media
    {"product_id": 31, "quantity": 60,  "warehouse": "main"},  # The Pragmatic Programmer
    {"product_id": 32, "quantity": 70,  "warehouse": "main"},  # Clean Code
    {"product_id": 33, "quantity": 50,  "warehouse": "main"},  # Designing Data-Intensive Applications
    {"product_id": 34, "quantity": 80,  "warehouse": "main"},  # The Phoenix Project
    {"product_id": 35, "quantity": 45,  "warehouse": "main"},  # Kubernetes in Action
    # Clothing & Accessories
    {"product_id": 36, "quantity": 100, "warehouse": "main"},  # Merino Wool Beanie
    {"product_id": 37, "quantity": 65,  "warehouse": "main"},  # Leather Bifold Wallet
    {"product_id": 38, "quantity": 90,  "warehouse": "main"},  # Canvas Tote Bag
    {"product_id": 39, "quantity": 85,  "warehouse": "main"},  # Running Cap
    {"product_id": 40, "quantity": 120, "warehouse": "main"},  # Compression Socks
    {"product_id": 41, "quantity": 45,  "warehouse": "main"},  # Fleece Zip Jacket
    {"product_id": 42, "quantity": 70,  "warehouse": "main"},  # Polarised Sunglasses
    # Health & Beauty
    {"product_id": 43, "quantity": 95,  "warehouse": "main"},  # Automatic Soap Dispenser
    {"product_id": 44, "quantity": 55,  "warehouse": "main"},  # Sonic Electric Toothbrush
    {"product_id": 45, "quantity": 130, "warehouse": "main"},  # Vitamin D3 Supplement
    {"product_id": 46, "quantity": 80,  "warehouse": "main"},  # Contoured Sleep Mask
    {"product_id": 47, "quantity": 40,  "warehouse": "main"},  # Posture Corrector
    # Office & Productivity
    {"product_id": 48, "quantity": 60,  "warehouse": "main"},  # Bamboo Desk Organiser
    {"product_id": 49, "quantity": 75,  "warehouse": "main"},  # Gel Wrist Rest
    {"product_id": 50, "quantity": 50,  "warehouse": "main"},  # Blue Light Glasses
    {"product_id": 51, "quantity": 25,  "warehouse": "main"},  # Dry-Erase Wall Calendar
    {"product_id": 52, "quantity": 45,  "warehouse": "main"},  # Cable Management Box
    # Toys & Games
    {"product_id": 53, "quantity": 30,  "warehouse": "main"},  # Tournament Chess Set
    {"product_id": 54, "quantity": 55,  "warehouse": "main"},  # 1000-Piece Jigsaw Puzzle
    {"product_id": 55, "quantity": 70,  "warehouse": "main"},  # Fast-Paced Card Game
    {"product_id": 56, "quantity": 90,  "warehouse": "main"},  # Speed Cube
    {"product_id": 57, "quantity": 35,  "warehouse": "main"},  # Tabletop Strategy Game
]

app = create_app()


def seed():
    with app.app_context():
        db.create_all()
        if Inventory.query.first():
            print("Inventory already has data. Skipping seed.")
            return

        for s in STOCK:
            db.session.add(Inventory(**s))

        db.session.commit()
        print(f"Seeded {len(STOCK)} inventory records.")


if __name__ == "__main__":
    seed()
