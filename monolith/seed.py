"""Seed script to populate the database with sample data."""
import os
import shutil
import uuid
from app import create_app
from services.catalog.models import db, Product
from services.inventory.models import Inventory

SEED_IMAGES_DIR = os.path.join(os.path.dirname(__file__), "seed_images")
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "static", "uploads")

app = create_app()

PRODUCTS = [
    # Electronics
    {"name": "Wireless Headphones", "description": "Noise-cancelling over-ear headphones with 30hr battery life.", "price": 79.99, "image": "headphones.jpg"},
    {"name": "Mechanical Keyboard", "description": "RGB mechanical keyboard with Cherry MX switches.", "price": 129.99, "image": "keyboard.jpg"},
    {"name": "USB-C Hub", "description": "7-in-1 USB-C hub with HDMI, USB 3.0, and SD card reader.", "price": 49.99, "image": "usb-hub.jpg"},
    {"name": "Laptop Stand", "description": "Adjustable aluminum laptop stand for ergonomic viewing.", "price": 34.99, "image": "laptop-stand.jpg"},
    {"name": "Webcam HD", "description": "1080p webcam with built-in microphone and auto-focus.", "price": 59.99, "image": "webcam.jpg"},
    {"name": "Smart Watch", "description": "Fitness tracker with heart rate monitor, GPS, and 7-day battery.", "price": 149.99, "image": "smart-watch.jpg"},
    {"name": "Portable Bluetooth Speaker", "description": "Waterproof wireless speaker with 12hr playtime and 360 sound.", "price": 39.99, "image": "bluetooth-speaker.jpg"},
    {"name": "Noise-Cancelling Earbuds", "description": "True wireless earbuds with ANC and 24hr total battery via charging case.", "price": 89.99, "image": "earbuds.jpg"},
    {"name": "4K Action Camera", "description": "Waterproof 4K action camera with electronic image stabilisation.", "price": 119.99, "image": "action-camera.jpg"},
    {"name": "Smart Home Hub", "description": "Voice-controlled smart home hub compatible with Alexa and Google Home.", "price": 49.99, "image": "smart-home-hub.jpg"},
    {"name": "Wireless Charging Pad", "description": "15W fast wireless charger compatible with all Qi-enabled devices.", "price": 24.99, "image": "wireless-charger.jpg"},
    {"name": "E-Reader", "description": "6-inch e-ink display with adjustable warm light and weeks of battery.", "price": 129.99, "image": "e-reader.jpg"},
    {"name": "Portable Power Bank", "description": "20,000mAh power bank with USB-C PD fast charge and dual outputs.", "price": 44.99, "image": "power-bank.jpg"},
    {"name": "LED Desk Lamp", "description": "Touch-controlled LED lamp with 5 colour temperatures and USB charging port.", "price": 32.99, "image": "desk-lamp.jpg"},
    {"name": "Digital Photo Frame", "description": "10-inch WiFi digital photo frame with cloud sync and auto-rotate.", "price": 69.99, "image": "photo-frame.jpg"},

    # Home & Kitchen
    {"name": "Stainless Steel Water Bottle", "description": "32oz vacuum-insulated bottle that keeps drinks cold 24hrs or hot 12hrs.", "price": 27.99, "image": "water-bottle.jpg"},
    {"name": "Coffee Grinder", "description": "Burr coffee grinder with 15 grind settings from espresso to French press.", "price": 54.99, "image": "coffee-grinder.jpg"},
    {"name": "Air Purifier", "description": "True HEPA air purifier covering up to 500 sq ft with sleep mode.", "price": 89.99, "image": "air-purifier.jpg"},
    {"name": "Bamboo Cutting Board", "description": "Extra-large bamboo cutting board with deep juice grooves and handle.", "price": 29.99, "image": "cutting-board.jpg"},
    {"name": "Cast Iron Skillet", "description": "Pre-seasoned 12-inch cast iron skillet suitable for all cooktops.", "price": 39.99, "image": "cast-iron-skillet.jpg"},
    {"name": "Instant Pot", "description": "6-quart 7-in-1 electric pressure cooker, slow cooker, and rice cooker.", "price": 79.99, "image": "instant-pot.jpg"},
    {"name": "Sous Vide Precision Cooker", "description": "1200W immersion circulator with WiFi control and precise temperature.", "price": 99.99, "image": "sous-vide.jpg"},
    {"name": "Handheld Vacuum", "description": "Cordless handheld vacuum with HEPA filter and 20-min runtime.", "price": 49.99, "image": "handheld-vacuum.jpg"},

    # Sports & Outdoors
    {"name": "Resistance Bands Set", "description": "Set of 5 latex resistance bands with door anchor and carrying bag.", "price": 19.99, "image": "resistance-bands.jpg"},
    {"name": "Yoga Mat", "description": "Non-slip 6mm thick yoga mat with alignment lines and carry strap.", "price": 34.99, "image": "yoga-mat.jpg"},
    {"name": "Jump Rope", "description": "Speed jump rope with ball-bearing handles and adjustable cable length.", "price": 14.99, "image": "jump-rope.jpg"},
    {"name": "Foam Roller", "description": "High-density foam roller for deep-tissue muscle recovery and stretching.", "price": 24.99, "image": "foam-roller.jpg"},
    {"name": "Hiking Backpack", "description": "40L waterproof hiking backpack with rain cover and ergonomic frame.", "price": 74.99, "image": "hiking-backpack.jpg"},
    {"name": "Trekking Poles", "description": "Pair of adjustable lightweight aluminum trekking poles with cork grips.", "price": 44.99, "image": "trekking-poles.jpg"},
    {"name": "Hydration Pack", "description": "2L hydration pack with insulated reservoir and multiple storage pockets.", "price": 39.99, "image": "hydration-pack.jpg"},

    # Books & Media
    {"name": "The Pragmatic Programmer", "description": "Classic software engineering guide covering best practices and career growth.", "price": 49.99, "image": "pragmatic-programmer.jpg"},
    {"name": "Clean Code", "description": "Robert C. Martin's handbook of agile software craftsmanship.", "price": 44.99, "image": "clean-code.jpg"},
    {"name": "Designing Data-Intensive Applications", "description": "Comprehensive guide to building reliable, scalable, and maintainable systems.", "price": 54.99, "image": "designing-data-apps.jpg"},
    {"name": "The Phoenix Project", "description": "A novel about IT, DevOps, and helping the business win.", "price": 29.99, "image": "phoenix-project.jpg"},
    {"name": "Kubernetes in Action", "description": "In-depth guide to deploying and managing containerised applications with Kubernetes.", "price": 59.99, "image": "kubernetes-in-action.jpg"},

    # Clothing & Accessories
    {"name": "Merino Wool Beanie", "description": "Soft 100% merino wool beanie, naturally temperature-regulating, one size fits all.", "price": 22.99, "image": "merino-beanie.jpg"},
    {"name": "Leather Bifold Wallet", "description": "Slim genuine leather bifold wallet with RFID-blocking lining and 8 card slots.", "price": 34.99, "image": "leather-wallet.jpg"},
    {"name": "Canvas Tote Bag", "description": "Heavy-duty 12oz canvas tote bag with zip interior pocket and reinforced handles.", "price": 18.99, "image": "canvas-tote.jpg"},
    {"name": "Running Cap", "description": "Lightweight moisture-wicking running cap with UV50+ protection and reflective detail.", "price": 19.99, "image": "running-cap.jpg"},
    {"name": "Compression Socks", "description": "3-pack graduated compression socks for travel, running, and long days on your feet.", "price": 24.99, "image": "compression-socks.jpg"},
    {"name": "Fleece Zip Jacket", "description": "Lightweight anti-pill fleece full-zip jacket with two zip pockets.", "price": 54.99, "image": "fleece-jacket.jpg"},
    {"name": "Polarised Sunglasses", "description": "UV400 polarised sunglasses with spring hinges and shatterproof lenses.", "price": 29.99, "image": "sunglasses.jpg"},

    # Health & Beauty
    {"name": "Automatic Soap Dispenser", "description": "Touchless foam soap dispenser with adjustable volume and rechargeable battery.", "price": 21.99, "image": "soap-dispenser.jpg"},
    {"name": "Sonic Electric Toothbrush", "description": "Sonic electric toothbrush with 3 replacement heads and 2-minute smart timer.", "price": 49.99, "image": "electric-toothbrush.jpg"},
    {"name": "Vitamin D3 Supplement", "description": "5000IU Vitamin D3 softgels with olive oil for absorption, 365-count bottle.", "price": 18.99, "image": "vitamin-d3.jpg"},
    {"name": "Contoured Sleep Mask", "description": "3D contoured sleep mask with adjustable strap and foam earplugs included.", "price": 14.99, "image": "sleep-mask.jpg"},
    {"name": "Posture Corrector", "description": "Adjustable back posture corrector brace for upper back and shoulder support.", "price": 27.99, "image": "posture-corrector.jpg"},

    # Office & Productivity
    {"name": "Bamboo Desk Organiser", "description": "6-compartment bamboo desktop organiser for pens, notes, and accessories.", "price": 26.99, "image": "desk-organiser.jpg"},
    {"name": "Gel Wrist Rest", "description": "Memory foam gel wrist rest with non-slip base for keyboard comfort.", "price": 16.99, "image": "wrist-rest.jpg"},
    {"name": "Blue Light Glasses", "description": "Anti-blue-light blocking glasses with clear lenses for screen use.", "price": 23.99, "image": "blue-light-glasses.jpg"},
    {"name": "Dry-Erase Wall Calendar", "description": "Large monthly dry-erase calendar whiteboard with marker and eraser.", "price": 34.99, "image": "wall-calendar.jpg"},
    {"name": "Cable Management Box", "description": "Large cable management box with cord organiser inserts, wood-finish lid.", "price": 22.99, "image": "cable-management.jpg"},

    # Toys & Games
    {"name": "Tournament Chess Set", "description": "Weighted Staunton-style chess pieces with roll-up vinyl board and timer.", "price": 44.99, "image": "chess-set.jpg"},
    {"name": "1000-Piece Jigsaw Puzzle", "description": "1000-piece landscape jigsaw puzzle with premium linen finish pieces.", "price": 19.99, "image": "jigsaw-puzzle.jpg"},
    {"name": "Fast-Paced Card Game", "description": "Hilarious quick-fire card game for 2-6 players, ages 7 and up.", "price": 14.99, "image": "card-game.jpg"},
    {"name": "Speed Cube", "description": "3x3 speed cube with adjustable tension and corner-cutting design.", "price": 12.99, "image": "speed-cube.jpg"},
    {"name": "Tabletop Strategy Game", "description": "Area-control strategy board game for 2-4 players with 60-90 min playtime.", "price": 39.99, "image": "strategy-game.jpg"},
]

STOCK = [
    50, 30, 100, 75, 45,   # Electronics (original 5)
    40, 60, 55, 25, 70,    # Electronics (new)
    90, 35, 80, 65, 30,    # Electronics (new)
    120, 45, 30, 85, 50,   # Home & Kitchen
    40, 20, 35,            # Home & Kitchen (cont.)
    110, 95, 150, 75, 40,  # Sports & Outdoors
    30, 55,                # Sports & Outdoors (cont.)
    60, 70, 50, 80, 45,    # Books & Media
    100, 65, 90, 85, 120,  # Clothing & Accessories
    45, 70,                # Clothing & Accessories (cont.)
    95, 55, 130, 80, 40,   # Health & Beauty
    60, 75, 50, 25, 45,    # Office & Productivity
    30, 55, 70, 90, 35,    # Toys & Games
]

with app.app_context():
    db.create_all()

    if Product.query.first():
        print("Database already has data. Skipping seed.")
    else:
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        for i, p in enumerate(PRODUCTS):
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
            db.session.flush()
            inv = Inventory(product_id=product.id, quantity=STOCK[i], warehouse="main")
            db.session.add(inv)

        db.session.commit()
        print(f"Seeded {len(PRODUCTS)} products with inventory.")
