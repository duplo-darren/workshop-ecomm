"""Seed the catalog database with sample products."""
import os
import shutil
import uuid
from .app import create_app
from .models import db, Product

SEED_IMAGES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "seed_images")
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "static", "uploads")

PRODUCTS = [
    # Electronics
    {"name": "Wireless Headphones", "description": "Noise-cancelling over-ear headphones with 30hr battery life.", "price": 79.99, "image": "headphones.jpg"},
    {"name": "Mechanical Keyboard", "description": "RGB mechanical keyboard with Cherry MX switches.", "price": 129.99, "image": "keyboard.jpg"},
    {"name": "USB-C Hub", "description": "7-in-1 USB-C hub with HDMI, USB 3.0, and SD card reader.", "price": 49.99, "image": "usb-hub.jpg"},
    {"name": "Laptop Stand", "description": "Adjustable aluminum laptop stand for ergonomic viewing.", "price": 34.99, "image": "laptop-stand.jpg"},
    {"name": "Webcam HD", "description": "1080p webcam with built-in microphone and auto-focus.", "price": 59.99, "image": "webcam.jpg"},
    {"name": "Smart Watch", "description": "Fitness tracker with heart rate monitor, GPS, and 7-day battery.", "price": 149.99},
    {"name": "Portable Bluetooth Speaker", "description": "Waterproof wireless speaker with 12hr playtime and 360 sound.", "price": 39.99},
    {"name": "Noise-Cancelling Earbuds", "description": "True wireless earbuds with ANC and 24hr total battery via charging case.", "price": 89.99},
    {"name": "4K Action Camera", "description": "Waterproof 4K action camera with electronic image stabilisation.", "price": 119.99},
    {"name": "Smart Home Hub", "description": "Voice-controlled smart home hub compatible with Alexa and Google Home.", "price": 49.99},
    {"name": "Wireless Charging Pad", "description": "15W fast wireless charger compatible with all Qi-enabled devices.", "price": 24.99},
    {"name": "E-Reader", "description": "6-inch e-ink display with adjustable warm light and weeks of battery.", "price": 129.99},
    {"name": "Portable Power Bank", "description": "20,000mAh power bank with USB-C PD fast charge and dual outputs.", "price": 44.99},
    {"name": "LED Desk Lamp", "description": "Touch-controlled LED lamp with 5 colour temperatures and USB charging port.", "price": 32.99},
    {"name": "Digital Photo Frame", "description": "10-inch WiFi digital photo frame with cloud sync and auto-rotate.", "price": 69.99},

    # Home & Kitchen
    {"name": "Stainless Steel Water Bottle", "description": "32oz vacuum-insulated bottle that keeps drinks cold 24hrs or hot 12hrs.", "price": 27.99},
    {"name": "Coffee Grinder", "description": "Burr coffee grinder with 15 grind settings from espresso to French press.", "price": 54.99},
    {"name": "Air Purifier", "description": "True HEPA air purifier covering up to 500 sq ft with sleep mode.", "price": 89.99},
    {"name": "Bamboo Cutting Board", "description": "Extra-large bamboo cutting board with deep juice grooves and handle.", "price": 29.99},
    {"name": "Cast Iron Skillet", "description": "Pre-seasoned 12-inch cast iron skillet suitable for all cooktops.", "price": 39.99},
    {"name": "Instant Pot", "description": "6-quart 7-in-1 electric pressure cooker, slow cooker, and rice cooker.", "price": 79.99},
    {"name": "Sous Vide Precision Cooker", "description": "1200W immersion circulator with WiFi control and precise temperature.", "price": 99.99},
    {"name": "Handheld Vacuum", "description": "Cordless handheld vacuum with HEPA filter and 20-min runtime.", "price": 49.99},

    # Sports & Outdoors
    {"name": "Resistance Bands Set", "description": "Set of 5 latex resistance bands with door anchor and carrying bag.", "price": 19.99},
    {"name": "Yoga Mat", "description": "Non-slip 6mm thick yoga mat with alignment lines and carry strap.", "price": 34.99},
    {"name": "Jump Rope", "description": "Speed jump rope with ball-bearing handles and adjustable cable length.", "price": 14.99},
    {"name": "Foam Roller", "description": "High-density foam roller for deep-tissue muscle recovery and stretching.", "price": 24.99},
    {"name": "Hiking Backpack", "description": "40L waterproof hiking backpack with rain cover and ergonomic frame.", "price": 74.99},
    {"name": "Trekking Poles", "description": "Pair of adjustable lightweight aluminum trekking poles with cork grips.", "price": 44.99},
    {"name": "Hydration Pack", "description": "2L hydration pack with insulated reservoir and multiple storage pockets.", "price": 39.99},

    # Books & Media
    {"name": "The Pragmatic Programmer", "description": "Classic software engineering guide covering best practices and career growth.", "price": 49.99},
    {"name": "Clean Code", "description": "Robert C. Martin's handbook of agile software craftsmanship.", "price": 44.99},
    {"name": "Designing Data-Intensive Applications", "description": "Comprehensive guide to building reliable, scalable, and maintainable systems.", "price": 54.99},
    {"name": "The Phoenix Project", "description": "A novel about IT, DevOps, and helping the business win.", "price": 29.99},
    {"name": "Kubernetes in Action", "description": "In-depth guide to deploying and managing containerised applications with Kubernetes.", "price": 59.99},

    # Clothing & Accessories
    {"name": "Merino Wool Beanie", "description": "Soft 100% merino wool beanie, naturally temperature-regulating, one size fits all.", "price": 22.99},
    {"name": "Leather Bifold Wallet", "description": "Slim genuine leather bifold wallet with RFID-blocking lining and 8 card slots.", "price": 34.99},
    {"name": "Canvas Tote Bag", "description": "Heavy-duty 12oz canvas tote bag with zip interior pocket and reinforced handles.", "price": 18.99},
    {"name": "Running Cap", "description": "Lightweight moisture-wicking running cap with UV50+ protection and reflective detail.", "price": 19.99},
    {"name": "Compression Socks", "description": "3-pack graduated compression socks for travel, running, and long days on your feet.", "price": 24.99},
    {"name": "Fleece Zip Jacket", "description": "Lightweight anti-pill fleece full-zip jacket with two zip pockets.", "price": 54.99},
    {"name": "Polarised Sunglasses", "description": "UV400 polarised sunglasses with spring hinges and shatterproof lenses.", "price": 29.99},

    # Health & Beauty
    {"name": "Automatic Soap Dispenser", "description": "Touchless foam soap dispenser with adjustable volume and rechargeable battery.", "price": 21.99},
    {"name": "Sonic Electric Toothbrush", "description": "Sonic electric toothbrush with 3 replacement heads and 2-minute smart timer.", "price": 49.99},
    {"name": "Vitamin D3 Supplement", "description": "5000IU Vitamin D3 softgels with olive oil for absorption, 365-count bottle.", "price": 18.99},
    {"name": "Contoured Sleep Mask", "description": "3D contoured sleep mask with adjustable strap and foam earplugs included.", "price": 14.99},
    {"name": "Posture Corrector", "description": "Adjustable back posture corrector brace for upper back and shoulder support.", "price": 27.99},

    # Office & Productivity
    {"name": "Bamboo Desk Organiser", "description": "6-compartment bamboo desktop organiser for pens, notes, and accessories.", "price": 26.99},
    {"name": "Gel Wrist Rest", "description": "Memory foam gel wrist rest with non-slip base for keyboard comfort.", "price": 16.99},
    {"name": "Blue Light Glasses", "description": "Anti-blue-light blocking glasses with clear lenses for screen use.", "price": 23.99},
    {"name": "Dry-Erase Wall Calendar", "description": "Large monthly dry-erase calendar whiteboard with marker and eraser.", "price": 34.99},
    {"name": "Cable Management Box", "description": "Large cable management box with cord organiser inserts, wood-finish lid.", "price": 22.99},

    # Toys & Games
    {"name": "Tournament Chess Set", "description": "Weighted Staunton-style chess pieces with roll-up vinyl board and timer.", "price": 44.99},
    {"name": "1000-Piece Jigsaw Puzzle", "description": "1000-piece landscape jigsaw puzzle with premium linen finish pieces.", "price": 19.99},
    {"name": "Fast-Paced Card Game", "description": "Hilarious quick-fire card game for 2-6 players, ages 7 and up.", "price": 14.99},
    {"name": "Speed Cube", "description": "3x3 speed cube with adjustable tension and corner-cutting design.", "price": 12.99},
    {"name": "Tabletop Strategy Game", "description": "Area-control strategy board game for 2-4 players with 60-90 min playtime.", "price": 39.99},
]

app = create_app()


def seed():
    with app.app_context():
        db.create_all()
        if Product.query.first():
            print("Catalog already has data. Skipping seed.")
            return

        os.makedirs(UPLOAD_DIR, exist_ok=True)
        for p in PRODUCTS:
            image_file = p.pop("image", None)
            if image_file:
                src = os.path.join(SEED_IMAGES_DIR, image_file)
                if os.path.exists(src):
                    ext = os.path.splitext(image_file)[1]
                    dest_name = f"{uuid.uuid4().hex}{ext}"
                    shutil.copy2(src, os.path.join(UPLOAD_DIR, dest_name))
                    p["image_path"] = f"uploads/{dest_name}"

            product = Product(**p)
            db.session.add(product)

        db.session.commit()
        print(f"Seeded {len(PRODUCTS)} products.")


if __name__ == "__main__":
    seed()
