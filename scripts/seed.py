#!/usr/bin/env python3
"""
VGP Platform — Boston Demo Data Seeder (Expanded)
══════════════════════════════════════════════════
Populates Auth, Inventory, and Buyer services with realistic Greater Boston
demo data across Food and Beauty/Fashion/Accessories categories.

Usage
─────
  cd vgp-platform
  python scripts/seed.py
"""

import asyncio
import sys
from datetime import datetime, timedelta, timezone

try:
    import httpx
except ImportError:
    print("ERROR: httpx not installed.  Run: pip install httpx", file=sys.stderr)
    sys.exit(1)

BASE    = "http://localhost:8000"
PASSWORD = "Test1234!"
TIMEOUT  = 30.0
CONCURRENCY = 4

def _exp(days: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()

def _ok(msg):   print(f"    ✓  {msg}")
def _skip(msg): print(f"    ~  {msg}  (already exists — skipped)")
def _warn(msg): print(f"    ⚠  {msg}")
def _err(msg):  print(f"    ✗  {msg}", file=sys.stderr)


# ── Retailers ──────────────────────────────────────────────────────────────────

RETAILERS: list[dict] = [
    # ── Food & Beverage ────────────────────────────────────────────────────────
    {"email": "dunkin@demo.com",          "name": "Dunkin"},
    {"email": "wholefoods@demo.com",      "name": "Whole Foods"},
    {"email": "stopshop@demo.com",        "name": "Stop & Shop"},
    {"email": "marketbasket@demo.com",    "name": "Market Basket"},
    {"email": "tatte@demo.com",           "name": "Tatte Bakery"},
    {"email": "mikespastry@demo.com",     "name": "Mike's Pastry"},
    {"email": "bostonbeer@demo.com",      "name": "Boston Beer Company"},
    {"email": "polar@demo.com",           "name": "Polar Beverages"},
    {"email": "panera@demo.com",          "name": "Panera Bread"},
    {"email": "sweetgreen@demo.com",      "name": "Sweetgreen"},
    {"email": "clover@demo.com",          "name": "Clover Food Lab"},
    {"email": "flour@demo.com",           "name": "Flour Bakery + Cafe"},
    {"email": "legalseafoods@demo.com",   "name": "Legal Sea Foods"},
    {"email": "traderjoes@demo.com",      "name": "Trader Joe's Boston"},
    {"email": "veggie@demo.com",          "name": "Veggie Galaxy"},
    {"email": "necoffee@demo.com",        "name": "New England Coffee"},
    {"email": "iggys@demo.com",           "name": "Iggy's Bread of the World"},
    {"email": "clearflour@demo.com",      "name": "Clear Flour Bread"},
    {"email": "davespasta@demo.com",      "name": "Dave's Fresh Pasta"},
    {"email": "formaggiokitchen@demo.com","name": "Formaggio Kitchen"},
    {"email": "harvestcoop@demo.com",     "name": "Harvest Co-op"},
    {"email": "pret@demo.com",            "name": "Pret A Manger"},
    {"email": "bonme@demo.com",           "name": "Bon Me"},
    {"email": "bgood@demo.com",           "name": "B.Good"},
    {"email": "dig@demo.com",             "name": "Dig"},
    {"email": "cheesecakefactory@demo.com","name": "The Cheesecake Factory"},
    {"email": "wegmans@demo.com",         "name": "Wegmans Boston"},
    {"email": "hannaford@demo.com",       "name": "Hannaford Supermarkets"},
    # ── Beauty, Makeup & Accessories ──────────────────────────────────────────
    {"email": "hm@demo.com",              "name": "H&M"},
    {"email": "newbalance@demo.com",      "name": "New Balance"},
    {"email": "tjx@demo.com",             "name": "TJX Companies"},
    {"email": "elf@demo.com",             "name": "e.l.f. Beauty"},
    {"email": "nyx@demo.com",             "name": "NYX Professional Makeup"},
    {"email": "revlon@demo.com",          "name": "Revlon"},
    {"email": "loreal@demo.com",          "name": "L'Oréal Boston"},
    {"email": "colourpop@demo.com",       "name": "ColourPop Cosmetics"},
    {"email": "physiciansformula@demo.com","name": "Physicians Formula"},
    {"email": "wetNwild@demo.com",        "name": "Wet n Wild"},
    {"email": "morphe@demo.com",          "name": "Morphe Cosmetics"},
    {"email": "charlottetilbury@demo.com","name": "Charlotte Tilbury Boston"},
    {"email": "sephora@demo.com",         "name": "Sephora Boston"},
    {"email": "lush@demo.com",            "name": "Lush Cosmetics Boston"},
    {"email": "zara@demo.com",            "name": "Zara Boston"},
    {"email": "urbanoutfitters@demo.com", "name": "Urban Outfitters Boston"},
    {"email": "freepeople@demo.com",      "name": "Free People Boston"},
    {"email": "express@demo.com",         "name": "Express Clothing"},
    {"email": "bananarepublic@demo.com",  "name": "Banana Republic Boston"},
    {"email": "gap@demo.com",             "name": "Gap Boston"},
    {"email": "forever21@demo.com",       "name": "Forever 21 Boston"},
    {"email": "bcbg@demo.com",            "name": "BCBG Max Azria"},
    {"email": "cvs@demo.com",             "name": "CVS Health"},
    {"email": "staples@demo.com",         "name": "Staples"},
    {"email": "bose@demo.com",            "name": "Bose"},
    # ── Men's Clothing & Footwear ──────────────────────────────────────────────
    {"email": "nike@demo.com",            "name": "Nike Boston"},
    {"email": "adidas@demo.com",          "name": "Adidas Boston"},
    {"email": "underarmour@demo.com",     "name": "Under Armour"},
    {"email": "levis@demo.com",           "name": "Levi's Boston"},
    {"email": "ralphlauren@demo.com",     "name": "Ralph Lauren Boston"},
    {"email": "tommyhilfiger@demo.com",   "name": "Tommy Hilfiger Boston"},
    {"email": "calvinklein@demo.com",     "name": "Calvin Klein Boston"},
    {"email": "americaneagle@demo.com",   "name": "American Eagle Outfitters"},
    {"email": "jcrew@demo.com",           "name": "J.Crew Boston"},
    {"email": "carhartt@demo.com",        "name": "Carhartt"},
    {"email": "patagonia@demo.com",       "name": "Patagonia Boston"},
    {"email": "northface@demo.com",       "name": "The North Face Boston"},
    {"email": "timberland@demo.com",      "name": "Timberland"},
    {"email": "columbia@demo.com",        "name": "Columbia Sportswear"},
    {"email": "lululemonmen@demo.com",    "name": "Lululemon Men's Boston"},
    {"email": "brooksbros@demo.com",      "name": "Brooks Brothers Boston"},
    {"email": "vineyard@demo.com",        "name": "Vineyard Vines Boston"},
    {"email": "uniqlo@demo.com",          "name": "Uniqlo Boston"},
    {"email": "rei@demo.com",             "name": "REI Boston"},
    {"email": "dickssporting@demo.com",   "name": "Dick's Sporting Goods Boston"},
    # ── Men's Grooming ────────────────────────────────────────────────────────
    {"email": "gillette@demo.com",        "name": "Gillette / P&G Boston"},
    {"email": "oldspice@demo.com",        "name": "Old Spice Men's Care"},
    {"email": "jackblack@demo.com",       "name": "Jack Black Men's Grooming"},
    {"email": "americancrew@demo.com",    "name": "American Crew"},
    {"email": "niveamen@demo.com",        "name": "Nivea Men Boston"},
    # ── More Food & Beverage ──────────────────────────────────────────────────
    {"email": "starbucks@demo.com",       "name": "Starbucks Boston"},
    {"email": "chipotle@demo.com",        "name": "Chipotle Boston"},
    {"email": "lacolombe@demo.com",       "name": "La Colombe Coffee Boston"},
    {"email": "finagle@demo.com",         "name": "Finagle A Bagel"},
    {"email": "bostonorganics@demo.com",  "name": "Boston Organics"},
    {"email": "boloco@demo.com",          "name": "Boloco Boston"},
    {"email": "shakeshack@demo.com",      "name": "Shake Shack Boston"},
    {"email": "bostonbaking@demo.com",    "name": "Boston Baking Co."},
    # ── More Beauty & Cosmetics ───────────────────────────────────────────────
    {"email": "glossier@demo.com",        "name": "Glossier Boston"},
    {"email": "fentybeauty@demo.com",     "name": "Fenty Beauty Boston"},
    {"email": "nars@demo.com",            "name": "NARS Cosmetics Boston"},
    {"email": "maccosmetics@demo.com",    "name": "MAC Cosmetics Boston"},
    {"email": "urbandecay@demo.com",      "name": "Urban Decay Boston"},
    {"email": "tartecosmetics@demo.com",  "name": "Tarte Cosmetics"},
    {"email": "toofaced@demo.com",        "name": "Too Faced Boston"},
    {"email": "benefit@demo.com",         "name": "Benefit Cosmetics Boston"},
    # ── Home Goods ────────────────────────────────────────────────────────────
    {"email": "cratebarrel@demo.com",     "name": "Crate & Barrel Boston"},
    {"email": "westelm@demo.com",         "name": "West Elm Boston"},
    {"email": "potterybarn@demo.com",     "name": "Pottery Barn Boston"},
    {"email": "athleta@demo.com",         "name": "Athleta Boston"},
]


# ── Inventory ──────────────────────────────────────────────────────────────────

INVENTORY: dict[str, list[dict]] = {

    # ── FOOD RETAILERS ────────────────────────────────────────────────────────

    "dunkin@demo.com": [
        {
            "title": "Surplus Assorted Pastries — Donuts, Muffins, Croissants",
            "category": "Food & Beverage",
            "quantity": 500,
            "price": 1.50,
            "condition": "good",
            "expiry_date": _exp(3),
            "description": "Assorted surplus baked goods and pastries from Dunkin locations across Greater Boston — donuts, muffins, and croissants. Fresh food packaged same-day. Ideal for food banks, shelters, and food rescue organizations.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus Dunkin Coffee Cups & Packaging (Sealed Cases)",
            "category": "Food & Beverage",
            "quantity": 300,
            "price": 0.75,
            "condition": "new",
            "expiry_date": _exp(90),
            "description": "Surplus sealed coffee cup cases from Dunkin supply chain overstock. New, unopened food-service packaging. Great for nonprofits running meal programs or food distribution events.",
            "location": "Canton, MA",
        },
        {
            "title": "Surplus Ground Coffee — Dunkin Original Blend",
            "category": "Beverages",
            "quantity": 400,
            "price": 3.00,
            "condition": "new",
            "expiry_date": _exp(180),
            "description": "Surplus Dunkin Original Blend ground coffee from overstock. Sealed bags, full shelf life. Excellent for food pantries, shelters, or resale. Coffee and beverages are always in demand.",
            "location": "Canton, MA",
        },
    ],

    "wholefoods@demo.com": [
        {
            "title": "Organic Fresh Produce Surplus — Seasonal Vegetables & Fruits",
            "category": "Produce",
            "quantity": 400,
            "price": 2.00,
            "condition": "good",
            "expiry_date": _exp(7),
            "description": "Mixed organic produce surplus from Whole Foods Boston-area stores — seasonal vegetables and fruits, slightly imperfect but fully edible fresh food. Excellent for food banks, food pantries, and produce distribution programs.",
            "location": "Cambridge, MA",
        },
        {
            "title": "Surplus Canned Goods — Beans, Soups, Vegetables",
            "category": "Canned Goods",
            "quantity": 250,
            "price": 1.50,
            "condition": "good",
            "expiry_date": _exp(365),
            "description": "Assorted surplus canned goods from Whole Foods Boston stores — beans, soups, vegetables. Label changes cleared for redistribution. Long shelf-life food items ideal for food pantries and emergency food programs.",
            "location": "Cambridge, MA",
        },
        {
            "title": "Surplus Prepared Hot Foods — Rotisserie & Deli",
            "category": "Prepared Foods",
            "quantity": 100,
            "price": 4.00,
            "condition": "good",
            "expiry_date": _exp(2),
            "description": "Surplus prepared hot food items including rotisserie chicken and deli-counter items from Whole Foods. Same-day prepared food, ideal for meal programs and immediate food distribution.",
            "location": "Boston, MA",
        },
    ],

    "stopshop@demo.com": [
        {
            "title": "Packaged Groceries Surplus — Crackers, Cereals, Pasta",
            "category": "Packaged Groceries",
            "quantity": 600,
            "price": 1.00,
            "condition": "good",
            "expiry_date": _exp(60),
            "description": "Assorted packaged grocery surplus from Stop & Shop stores across Greater Boston — crackers, cereals, snack foods, pasta. Non-perishable food staples ideal for food pantries and food distribution programs.",
            "location": "Quincy, MA",
        },
        {
            "title": "Dairy Products Surplus — Milk, Yogurt, Cheese",
            "category": "Dairy",
            "quantity": 300,
            "price": 2.00,
            "condition": "good",
            "expiry_date": _exp(7),
            "description": "Surplus dairy products from Stop & Shop Boston stores — milk, yogurt, and cheese nearing sell-by date but fully safe. Fresh food ideal for immediate food distribution and meal programs.",
            "location": "Quincy, MA",
        },
    ],

    "marketbasket@demo.com": [
        {
            "title": "Bulk Dry Goods Surplus — Rice, Flour, Pasta, Grains",
            "category": "Bulk Dry Goods",
            "quantity": 800,
            "price": 0.80,
            "condition": "good",
            "expiry_date": _exp(180),
            "description": "Bulk dry goods surplus from Market Basket regional distribution — rice, flour, pasta, and grains. Long-shelf-life food staples ideal for food banks, food pantries, and bulk food buyers.",
            "location": "Tewksbury, MA",
        },
        {
            "title": "Household & Cleaning Supplies Surplus",
            "category": "Household Essentials",
            "quantity": 400,
            "price": 1.20,
            "condition": "good",
            "expiry_date": _exp(365),
            "description": "Surplus household essentials from Market Basket — cleaning supplies, paper goods, and laundry products from overstock clearance. Useful for shelters and community organizations.",
            "location": "Tewksbury, MA",
        },
    ],

    "tatte@demo.com": [
        {
            "title": "Surplus Tatte Pastries — Kouign-Amann, Croissants, Galettes",
            "category": "Baked Goods",
            "quantity": 150,
            "price": 2.00,
            "condition": "good",
            "expiry_date": _exp(2),
            "description": "Daily surplus pastries from Tatte Bakery Boston locations — kouign-amann, croissants, and galettes des rois. Artisan baked goods, fresh food perfect for shelters, food rescue, or same-day redistribution.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus Artisan Sourdough & Specialty Bread",
            "category": "Baked Goods",
            "quantity": 80,
            "price": 3.00,
            "condition": "good",
            "expiry_date": _exp(2),
            "description": "Surplus artisan sourdough and specialty breads from Tatte Bakery — baked fresh daily, leftover after close. Fresh baked food ideal for shelters, food banks, or food rescue organizations.",
            "location": "Boston, MA",
        },
    ],

    "mikespastry@demo.com": [
        {
            "title": "Surplus Cannoli — Traditional, Chocolate, Pistachio",
            "category": "Baked Goods",
            "quantity": 200,
            "price": 4.00,
            "condition": "good",
            "expiry_date": _exp(3),
            "description": "Surplus cannoli from Mike's Pastry North End location — traditional, chocolate, and pistachio flavors. Fresh Italian baked goods and pastries perfect for food rescue, community events, or resale.",
            "location": "Boston, MA (North End)",
        },
        {
            "title": "Surplus Italian Cookies — Pignoli, Rainbow, Anisette",
            "category": "Baked Goods",
            "quantity": 150,
            "price": 2.00,
            "condition": "good",
            "expiry_date": _exp(7),
            "description": "Assorted surplus Italian cookies from Mike's Pastry — pignoli, rainbow, and anisette varieties. Fresh baked goods ideal for food distribution, shelters, or resale.",
            "location": "Boston, MA (North End)",
        },
    ],

    "bostonbeer@demo.com": [
        {
            "title": "Samuel Adams Beer Cases — Seasonal Surplus Variety Packs",
            "category": "Beverages",
            "quantity": 500,
            "price": 18.00,
            "condition": "new",
            "expiry_date": _exp(90),
            "description": "Surplus Samuel Adams beer cases from Boston Beer Company — seasonal variety packs and flagship brews cleared for redistribution. Beverages ideal for resellers, event organizers, or licensed retailers.",
            "location": "Jamaica Plain, MA",
        },
    ],

    "polar@demo.com": [
        {
            "title": "Polar Sparkling Water — Surplus Assorted Flavor Cases",
            "category": "Beverages",
            "quantity": 700,
            "price": 6.00,
            "condition": "new",
            "expiry_date": _exp(180),
            "description": "Surplus Polar Beverages sparkling water cases from Worcester production — assorted flavors including lime, cranberry-lime, and raspberry. Beverages suitable for resellers, food pantries, or community events.",
            "location": "Worcester, MA",
        },
    ],

    "panera@demo.com": [
        {
            "title": "Surplus Panera Bagels, Muffins & Baked Goods",
            "category": "Baked Goods",
            "quantity": 300,
            "price": 1.00,
            "condition": "good",
            "expiry_date": _exp(2),
            "description": "Daily surplus baked goods from Panera Bread Boston locations — bagels, muffins, pastries, and sourdough bread. Fresh food available for food rescue, shelters, and food banks. Packaged end-of-day.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus Panera Soups & Mac and Cheese — Refrigerated",
            "category": "Prepared Foods",
            "quantity": 150,
            "price": 3.00,
            "condition": "good",
            "expiry_date": _exp(3),
            "description": "Surplus refrigerated soups and mac and cheese from Panera Bread Boston. Prepared food items including broccoli cheddar soup, chicken noodle, and creamy tomato. Ideal for food banks, shelters, and meal programs.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus Panera Salad Kits & Grain Bowls",
            "category": "Prepared Foods",
            "quantity": 100,
            "price": 3.50,
            "condition": "good",
            "expiry_date": _exp(2),
            "description": "Surplus packaged salad kits and grain bowls from Panera Bread Boston stores. Fresh food ingredients including greens, proteins, and dressings. Great for food rescue and immediate distribution.",
            "location": "Boston, MA",
        },
    ],

    "sweetgreen@demo.com": [
        {
            "title": "Surplus Sweetgreen Organic Greens & Salad Mix",
            "category": "Produce",
            "quantity": 200,
            "price": 2.50,
            "condition": "good",
            "expiry_date": _exp(3),
            "description": "Surplus organic greens and salad mix from Sweetgreen Boston locations — kale, arugula, romaine, spinach. Fresh produce suitable for food banks, community kitchens, and food rescue organizations.",
            "location": "Boston, MA",
        },
    ],

    "clover@demo.com": [
        {
            "title": "Surplus Clover Vegetarian Meal Kits & Wraps",
            "category": "Prepared Foods",
            "quantity": 120,
            "price": 4.00,
            "condition": "good",
            "expiry_date": _exp(2),
            "description": "Surplus vegetarian meal kits, sandwiches, and wraps from Clover Food Lab Boston. Fresh plant-based food including falafel wraps, BBQ seitan, and chickpea fritter sandwiches. Ideal for food rescue programs.",
            "location": "Cambridge, MA",
        },
        {
            "title": "Surplus Clover Grain Bowls & Side Salads",
            "category": "Prepared Foods",
            "quantity": 80,
            "price": 3.00,
            "condition": "good",
            "expiry_date": _exp(2),
            "description": "Surplus grain bowls and side salads from Clover Food Lab — brown rice bowls, roasted vegetable sides, and hummus platters. Fresh prepared food perfect for shelters and meal programs.",
            "location": "Boston, MA",
        },
    ],

    "flour@demo.com": [
        {
            "title": "Surplus Flour Bakery Sticky Buns & Pastries",
            "category": "Baked Goods",
            "quantity": 100,
            "price": 3.50,
            "condition": "good",
            "expiry_date": _exp(2),
            "description": "Surplus pastries and baked goods from Flour Bakery + Cafe Boston — famous sticky buns, banana bread, tarts, and cookies. Award-winning fresh baked goods ideal for food rescue and distribution.",
            "location": "South End, Boston, MA",
        },
        {
            "title": "Surplus Flour Bakery Sandwich Bread & Rolls",
            "category": "Baked Goods",
            "quantity": 60,
            "price": 4.00,
            "condition": "good",
            "expiry_date": _exp(2),
            "description": "Surplus artisan sandwich bread and dinner rolls from Flour Bakery + Cafe. Fresh baked goods from one of Boston's top bakeries — ideal for shelters, food banks, and food rescue organizations.",
            "location": "South End, Boston, MA",
        },
    ],

    "legalseafoods@demo.com": [
        {
            "title": "Surplus Legal Sea Foods Clam Chowder — Frozen Gallons",
            "category": "Prepared Foods",
            "quantity": 80,
            "price": 12.00,
            "condition": "good",
            "expiry_date": _exp(90),
            "description": "Surplus frozen Legal Sea Foods New England clam chowder from Boston production — iconic Boston seafood food item. Bulk frozen gallons suitable for resellers, restaurants, and food programs.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus Legal Sea Foods Frozen Seafood — Mixed Case",
            "category": "Seafood",
            "quantity": 60,
            "price": 15.00,
            "condition": "good",
            "expiry_date": _exp(60),
            "description": "Surplus frozen seafood from Legal Sea Foods Boston — mixed cases of cod, haddock, and shrimp. Boston seafood staples ideal for food banks with freezer capacity, shelters, or resellers.",
            "location": "Boston, MA",
        },
    ],

    "traderjoes@demo.com": [
        {
            "title": "Surplus Trader Joe's Packaged Snacks & Trail Mix",
            "category": "Packaged Groceries",
            "quantity": 500,
            "price": 1.50,
            "condition": "good",
            "expiry_date": _exp(90),
            "description": "Surplus packaged snacks and trail mixes from Trader Joe's Boston — nuts, dried fruits, granola bars, crackers, and popcorn. Non-perishable food great for food pantries and snack programs.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus Trader Joe's Frozen Meals & Entrees",
            "category": "Prepared Foods",
            "quantity": 200,
            "price": 3.00,
            "condition": "good",
            "expiry_date": _exp(90),
            "description": "Surplus frozen meals and entrees from Trader Joe's Boston — Indian simmer sauces, pasta dishes, rice bowls, and soups. Frozen prepared food suitable for food banks with freezers and food rescue organizations.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus Trader Joe's Seasonal Specialty Items",
            "category": "Packaged Groceries",
            "quantity": 300,
            "price": 2.00,
            "condition": "good",
            "expiry_date": _exp(120),
            "description": "Surplus seasonal specialty packaged food items from Trader Joe's Boston — holiday cookies, specialty cheeses, charcuterie items, and themed snacks from seasonal inventory clearance.",
            "location": "Boston, MA",
        },
    ],

    "veggie@demo.com": [
        {
            "title": "Surplus Veggie Galaxy Vegan Comfort Food Trays",
            "category": "Prepared Foods",
            "quantity": 60,
            "price": 5.00,
            "condition": "good",
            "expiry_date": _exp(2),
            "description": "Surplus vegan comfort food trays from Veggie Galaxy Cambridge — vegan mac and cheese, jackfruit BBQ, and mushroom burgers. Fresh plant-based food ideal for vegan food programs and shelters.",
            "location": "Cambridge, MA",
        },
    ],

    "necoffee@demo.com": [
        {
            "title": "New England Coffee Whole Bean Surplus — Assorted Roasts",
            "category": "Beverages",
            "quantity": 600,
            "price": 5.00,
            "condition": "new",
            "expiry_date": _exp(180),
            "description": "Surplus whole bean and ground coffee from New England Coffee Malden production — light, medium, and dark roasts. Sealed bags of coffee beverages ideal for food pantries, resellers, and food service organizations.",
            "location": "Malden, MA",
        },
        {
            "title": "New England Coffee K-Cup Pods Surplus — Bulk Cases",
            "category": "Beverages",
            "quantity": 400,
            "price": 8.00,
            "condition": "new",
            "expiry_date": _exp(180),
            "description": "Surplus K-Cup coffee pod cases from New England Coffee — bulk overstock cases in assorted flavors. Coffee beverages ideal for office resellers, food pantries, and SMB buyers.",
            "location": "Malden, MA",
        },
    ],

    "iggys@demo.com": [
        {
            "title": "Surplus Iggy's Artisan Bread Loaves — Mixed Varieties",
            "category": "Baked Goods",
            "quantity": 150,
            "price": 3.00,
            "condition": "good",
            "expiry_date": _exp(3),
            "description": "Surplus artisan bread loaves from Iggy's Bread of the World Cambridge — ciabatta, sourdough, whole wheat, and olive loaves. Fresh baked goods ideal for food banks, shelters, and food rescue organizations.",
            "location": "Cambridge, MA",
        },
    ],

    "clearflour@demo.com": [
        {
            "title": "Surplus Clear Flour European-Style Pastries & Tarts",
            "category": "Baked Goods",
            "quantity": 80,
            "price": 4.00,
            "condition": "good",
            "expiry_date": _exp(2),
            "description": "Surplus European-style pastries and tarts from Clear Flour Bread Brookline — pain au chocolat, fruit tarts, and Parisian-style baked goods. Fresh food ideal for food rescue and same-day distribution.",
            "location": "Brookline, MA",
        },
    ],

    "davespasta@demo.com": [
        {
            "title": "Surplus Fresh Pasta & Specialty Sauces",
            "category": "Prepared Foods",
            "quantity": 100,
            "price": 4.00,
            "condition": "good",
            "expiry_date": _exp(7),
            "description": "Surplus fresh pasta and specialty pasta sauces from Dave's Fresh Pasta Somerville — handmade fettuccine, ravioli, and marinara sauces. Refrigerated fresh food ideal for food banks or resale at farmers markets.",
            "location": "Somerville, MA",
        },
    ],

    "formaggiokitchen@demo.com": [
        {
            "title": "Surplus Artisan Cheese & Charcuterie — Mixed Selection",
            "category": "Dairy",
            "quantity": 50,
            "price": 10.00,
            "condition": "good",
            "expiry_date": _exp(14),
            "description": "Surplus artisan cheese and charcuterie from Formaggio Kitchen Cambridge — imported and domestic cheeses, cured meats, and specialty dairy. Premium food items ideal for upscale food resellers, caterers, or food rescue.",
            "location": "Cambridge, MA",
        },
    ],

    "harvestcoop@demo.com": [
        {
            "title": "Surplus Organic Bulk Grains & Legumes",
            "category": "Bulk Dry Goods",
            "quantity": 300,
            "price": 1.50,
            "condition": "good",
            "expiry_date": _exp(365),
            "description": "Surplus organic bulk dry goods from Harvest Co-op Boston and Jamaica Plain — lentils, chickpeas, brown rice, quinoa, and oats. Staple food items ideal for food banks, community kitchens, and bulk food buyers.",
            "location": "Jamaica Plain, MA",
        },
        {
            "title": "Surplus Natural & Organic Packaged Goods",
            "category": "Packaged Groceries",
            "quantity": 200,
            "price": 2.50,
            "condition": "good",
            "expiry_date": _exp(120),
            "description": "Surplus natural and organic packaged food from Harvest Co-op — granola, nut butters, herbal teas, and specialty health foods. Organic food pantry staples suitable for health-focused food programs.",
            "location": "Jamaica Plain, MA",
        },
    ],

    "pret@demo.com": [
        {
            "title": "Surplus Pret A Manger Sandwiches & Wraps",
            "category": "Prepared Foods",
            "quantity": 200,
            "price": 2.00,
            "condition": "good",
            "expiry_date": _exp(1),
            "description": "Daily surplus fresh sandwiches and wraps from Pret A Manger Boston — made fresh each morning without preservatives. Perishable food perfect for same-day food rescue, shelters, and meal programs.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus Pret Salads, Fruit Cups & Snacks",
            "category": "Prepared Foods",
            "quantity": 100,
            "price": 2.00,
            "condition": "good",
            "expiry_date": _exp(1),
            "description": "Daily surplus packaged salads, fruit cups, and yogurt parfaits from Pret A Manger Boston. Fresh food including superfood salads, mixed berry cups, and overnight oats. Ideal for immediate food distribution.",
            "location": "Boston, MA",
        },
    ],

    "bonme@demo.com": [
        {
            "title": "Surplus Bon Me Vietnamese Street Food — Banh Mi & Bowls",
            "category": "Prepared Foods",
            "quantity": 80,
            "price": 4.00,
            "condition": "good",
            "expiry_date": _exp(2),
            "description": "Surplus Vietnamese street food from Bon Me Boston — banh mi sandwiches, rice bowls, and noodle salads. Freshly made food with proteins, pickled vegetables, and herbs. Great for food rescue and shelter meal programs.",
            "location": "Boston, MA",
        },
    ],

    "bgood@demo.com": [
        {
            "title": "Surplus B.Good Fresh Burgers & Grain Bowls",
            "category": "Prepared Foods",
            "quantity": 60,
            "price": 5.00,
            "condition": "good",
            "expiry_date": _exp(1),
            "description": "Surplus fresh-made burgers and grain bowls from B.Good Boston — real food burgers, roasted vegetable bowls, and local farm ingredients. Prepared food ideal for same-day food rescue and community meal programs.",
            "location": "Boston, MA",
        },
    ],

    "dig@demo.com": [
        {
            "title": "Surplus Dig Roasted Vegetables & Proteins",
            "category": "Prepared Foods",
            "quantity": 100,
            "price": 4.00,
            "condition": "good",
            "expiry_date": _exp(2),
            "description": "Surplus roasted seasonal vegetables and proteins from Dig Boston — farm-to-table food including roasted squash, brussels sprouts, lemon chicken, and herb salmon. Fresh food for shelters and community meal programs.",
            "location": "Boston, MA",
        },
    ],

    "cheesecakefactory@demo.com": [
        {
            "title": "Surplus Cheesecake Factory Mini Cheesecakes — Assorted Flavors",
            "category": "Baked Goods",
            "quantity": 120,
            "price": 5.00,
            "condition": "good",
            "expiry_date": _exp(5),
            "description": "Surplus mini cheesecakes from The Cheesecake Factory Boston — original, strawberry, chocolate, and seasonal flavors. Premium dessert food items ideal for resellers, food rescue, and community events.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus Cheesecake Factory Bread Loaves & Rolls",
            "category": "Baked Goods",
            "quantity": 80,
            "price": 2.00,
            "condition": "good",
            "expiry_date": _exp(2),
            "description": "Surplus signature brown bread loaves and dinner rolls from The Cheesecake Factory Boston. Famous honey wheat bread — fresh baked goods suitable for food rescue and shelter meal programs.",
            "location": "Boston, MA",
        },
    ],

    "wegmans@demo.com": [
        {
            "title": "Surplus Wegmans Prepared Deli & Hot Bar Food",
            "category": "Prepared Foods",
            "quantity": 150,
            "price": 4.00,
            "condition": "good",
            "expiry_date": _exp(2),
            "description": "Surplus prepared deli and hot bar food from Wegmans Boston — rotisserie chicken, lasagna, sushi, and international cuisines. Ready-to-eat food ideal for same-day food rescue and meal distribution programs.",
            "location": "Chestnut Hill, MA",
        },
        {
            "title": "Surplus Wegmans Bakery — Artisan Breads & Desserts",
            "category": "Baked Goods",
            "quantity": 100,
            "price": 3.00,
            "condition": "good",
            "expiry_date": _exp(2),
            "description": "Surplus in-store bakery items from Wegmans Boston — artisan breads, cakes, cookies, and muffins. Fresh baked goods available for food banks, shelters, and food rescue organizations.",
            "location": "Chestnut Hill, MA",
        },
    ],

    "hannaford@demo.com": [
        {
            "title": "Surplus Hannaford Brand Canned Goods & Pantry Staples",
            "category": "Canned Goods",
            "quantity": 500,
            "price": 0.75,
            "condition": "good",
            "expiry_date": _exp(365),
            "description": "Surplus Hannaford private-label canned goods and pantry staples — canned tomatoes, beans, corn, tuna, and pasta sauces. Long shelf-life food pantry essentials ideal for food banks and emergency food programs.",
            "location": "Bedford, NH (serves Boston area)",
        },
        {
            "title": "Surplus Hannaford Fresh Bakery & Deli Items",
            "category": "Baked Goods",
            "quantity": 200,
            "price": 1.50,
            "condition": "good",
            "expiry_date": _exp(3),
            "description": "Surplus fresh bakery and deli items from Hannaford Supermarkets — sliced deli meats, cheese wheels, fresh bread, and bakery items. Refrigerated food perfect for food rescue and shelter meal programs.",
            "location": "Bedford, NH (serves Boston area)",
        },
    ],

    # ── BEAUTY, MAKEUP & FASHION RETAILERS ────────────────────────────────────

    "hm@demo.com": [
        {
            "title": "H&M Excess Women's Apparel — Mixed Sizes, New with Tags",
            "category": "Women's Clothing",
            "quantity": 500,
            "price": 5.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Excess new women's apparel from H&M seasonal inventory clearance — mixed sizes and styles, original tags still attached. Women's clothing including tops, blouses, dresses, and outerwear. Great for nonprofits, resellers, and thrift stores.",
            "location": "Boston, MA",
        },
        {
            "title": "H&M Excess Men's & Kids' Clothing — Seasonal Clearance",
            "category": "Apparel",
            "quantity": 300,
            "price": 4.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Excess new men's and kids' clothing from H&M Boston — t-shirts, jeans, hoodies, and jackets. Mixed sizes, new with tags. Surplus apparel and clothing suitable for resellers, shelters, and donation programs.",
            "location": "Boston, MA",
        },
    ],

    "newbalance@demo.com": [
        {
            "title": "Surplus New Balance Women's Athletic Shoes — Discontinued Lines",
            "category": "Women's Footwear",
            "quantity": 150,
            "price": 25.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus New Balance women's athletic shoes from Boston HQ — various styles and sizes from discontinued lines, factory new in original boxes. Women's footwear and athletic accessories at deep discount. Great for resellers.",
            "location": "Brighton, MA",
        },
        {
            "title": "Surplus New Balance Women's Athletic Apparel — Running & Training",
            "category": "Women's Athletic Apparel",
            "quantity": 300,
            "price": 15.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Excess New Balance women's athletic apparel and workout clothing from Brighton campus — women's running shirts, shorts, leggings, and sports bras. New with tags. Women's fitness accessories and activewear for resellers and nonprofits.",
            "location": "Brighton, MA",
        },
    ],

    "tjx@demo.com": [
        {
            "title": "TJX Mixed Women's Clothing Surplus — TJ Maxx & Marshalls",
            "category": "Women's Clothing",
            "quantity": 400,
            "price": 8.00,
            "condition": "like_new",
            "expiry_date": _exp(365),
            "description": "Mixed women's clothing surplus from TJX Companies — assorted women's styles and sizes from TJ Maxx and Marshalls inventory transitions. Women's tops, pants, dresses, and accessories. Like-new condition, great for resellers and nonprofits.",
            "location": "Framingham, MA",
        },
        {
            "title": "TJX Home Goods & Accessories Surplus — HomeGoods Overstock",
            "category": "Home Goods",
            "quantity": 300,
            "price": 6.00,
            "condition": "like_new",
            "expiry_date": _exp(365),
            "description": "Home goods and accessories surplus from TJX — kitchenware, decorative accessories, bedding, and women's handbags from TJ Maxx and HomeGoods inventory overstock. Great for resellers and thrift organizations.",
            "location": "Framingham, MA",
        },
    ],

    "elf@demo.com": [
        {
            "title": "e.l.f. Cosmetics Makeup Surplus — Lip, Eye & Face Products",
            "category": "Makeup & Cosmetics",
            "quantity": 600,
            "price": 3.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus e.l.f. Beauty makeup and cosmetics — lip gloss, mascara, eyeshadow palettes, foundation, and blush. Cruelty-free women's beauty and makeup products from packaging update overstock. Ideal for nonprofits serving women, resellers, and beauty programs.",
            "location": "Boston, MA",
        },
        {
            "title": "e.l.f. Cosmetics Skincare Surplus — Moisturizers, Serums & SPF",
            "category": "Beauty & Skincare",
            "quantity": 400,
            "price": 4.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus e.l.f. skincare and beauty products — moisturizers, vitamin C serums, eye creams, and SPF primers. Women's skincare and beauty essentials from overstock clearance. Great for nonprofits supporting women, beauty resellers.",
            "location": "Boston, MA",
        },
    ],

    "nyx@demo.com": [
        {
            "title": "NYX Professional Makeup Surplus — Lipstick, Liner & Palettes",
            "category": "Makeup & Cosmetics",
            "quantity": 500,
            "price": 5.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus NYX Professional Makeup cosmetics — Soft Matte Lip Cream, Epic Ink Liner, Ultimate Shadow Palettes, and setting spray. Professional-quality women's makeup from seasonal overstock. Perfect for resellers, beauty nonprofits, and women's shelters.",
            "location": "Boston, MA",
        },
        {
            "title": "NYX Makeup Accessories — Brushes, Sponges & Setting Spray",
            "category": "Beauty & Accessories",
            "quantity": 300,
            "price": 4.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus NYX beauty accessories and makeup tools — professional brush sets, beauty blender sponges, setting spray, and makeup bags. Women's beauty accessories from overstock clearance. Great for nonprofits and resellers.",
            "location": "Boston, MA",
        },
    ],

    "revlon@demo.com": [
        {
            "title": "Revlon Makeup Surplus — Foundation, Lipstick & Mascara",
            "category": "Makeup & Cosmetics",
            "quantity": 700,
            "price": 4.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Revlon cosmetics and makeup — ColorStay Foundation, Super Lustrous Lipstick, and CleanLiner mascara. Women's drugstore beauty and makeup staples from distribution overstock. Ideal for nonprofits, women's programs, and resellers.",
            "location": "Boston, MA",
        },
        {
            "title": "Revlon Hair Color & Hair Care Surplus",
            "category": "Beauty & Hair Care",
            "quantity": 300,
            "price": 5.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Revlon hair color and hair care products — ColorSilk hair dye, Realistic hair relaxer, and Flex conditioner. Women's beauty and hair care accessories from overstock. Good for resellers and nonprofits serving women.",
            "location": "Boston, MA",
        },
    ],

    "loreal@demo.com": [
        {
            "title": "L'Oréal Paris Makeup Surplus — Foundation, Mascara & Lip",
            "category": "Makeup & Cosmetics",
            "quantity": 600,
            "price": 6.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus L'Oréal Paris makeup and cosmetics — True Match Foundation, Voluminous Mascara, Infallible lipstick, and eyeshadow quads. Premium drugstore women's beauty and makeup from Boston distribution overstock. Ideal for resellers and nonprofits.",
            "location": "Boston, MA",
        },
        {
            "title": "L'Oréal Skincare Surplus — Revitalift, Collagen & SPF",
            "category": "Beauty & Skincare",
            "quantity": 400,
            "price": 8.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus L'Oréal Paris skincare and beauty products — Revitalift Derm Intensives, Collagen Moisture Filler, and Pure-Clay Mask. Women's anti-aging skincare from seasonal overstock. Excellent for resellers and nonprofits supporting women.",
            "location": "Boston, MA",
        },
    ],

    "colourpop@demo.com": [
        {
            "title": "ColourPop Cosmetics Surplus — Eyeshadow Palettes & Lippies",
            "category": "Makeup & Cosmetics",
            "quantity": 400,
            "price": 6.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus ColourPop cosmetics — eyeshadow palettes, Ultra Matte Lip, Super Shock Shadows, and blush. Affordable cruelty-free women's makeup from limited edition overstock. Perfect for beauty resellers, nonprofits, and women's programs.",
            "location": "Boston, MA",
        },
    ],

    "physiciansformula@demo.com": [
        {
            "title": "Physicians Formula Organic Wear Makeup Surplus",
            "category": "Makeup & Cosmetics",
            "quantity": 350,
            "price": 5.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Physicians Formula Organic Wear natural and hypoallergenic makeup — loose powder, blush, and mascara. Women's clean beauty and cosmetics from overstock. Ideal for eco-conscious nonprofits, resellers, and women's health programs.",
            "location": "Boston, MA",
        },
    ],

    "wetNwild@demo.com": [
        {
            "title": "Wet n Wild Makeup Surplus — Mega Last Lipstick & Color Icon",
            "category": "Makeup & Cosmetics",
            "quantity": 800,
            "price": 2.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Wet n Wild cosmetics — Mega Last Lipstick, Color Icon Eyeshadow Palettes, Photo Focus Foundation, and MegaGlo Highlighter. Affordable women's makeup from overstock. Great for nonprofits serving women, beauty programs, and resellers.",
            "location": "Boston, MA",
        },
    ],

    "morphe@demo.com": [
        {
            "title": "Morphe Cosmetics Surplus — Eyeshadow Palettes & Brushes",
            "category": "Makeup & Cosmetics",
            "quantity": 200,
            "price": 12.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Morphe professional makeup — 35-pan eyeshadow palettes, artist brush sets, and setting powder. Professional-quality women's makeup and beauty tools from influencer collaboration overstock. Excellent for beauty resellers and women's programs.",
            "location": "Boston, MA",
        },
        {
            "title": "Morphe Makeup Brush Sets & Accessories",
            "category": "Beauty & Accessories",
            "quantity": 150,
            "price": 10.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Morphe professional brush sets and makeup accessories — 12-piece brush sets, beauty sponges, and brush cleansers. Women's beauty tools and accessories from overstock clearance. Ideal for resellers and nonprofits supporting women.",
            "location": "Boston, MA",
        },
    ],

    "charlottetilbury@demo.com": [
        {
            "title": "Charlotte Tilbury Beauty Surplus — Pillow Talk & Iconic Sets",
            "category": "Makeup & Cosmetics",
            "quantity": 100,
            "price": 20.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Charlotte Tilbury luxury makeup and beauty — Pillow Talk lipstick, Magic Cream moisturizer, and Flawless Filter. Premium women's beauty and cosmetics from Boston boutique overstock. Excellent for luxury beauty resellers.",
            "location": "Boston, MA",
        },
    ],

    "sephora@demo.com": [
        {
            "title": "Sephora Collection Makeup Surplus — Palettes & Sets",
            "category": "Makeup & Cosmetics",
            "quantity": 200,
            "price": 10.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Sephora Collection house-brand makeup — eyeshadow palettes, blush trios, and holiday gift sets. Women's beauty and cosmetics from end-of-season clearance at Sephora Boston. Great for beauty resellers and nonprofits.",
            "location": "Boston, MA",
        },
        {
            "title": "Sephora Multi-Brand Skincare Surplus — Moisturizers & Serums",
            "category": "Beauty & Skincare",
            "quantity": 150,
            "price": 15.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus multi-brand skincare and beauty products from Sephora Boston — First Aid Beauty, Belif, Dr. Brandt moisturizers and serums. Women's skincare essentials from display model and overstock clearance. Perfect for beauty resellers.",
            "location": "Boston, MA",
        },
    ],

    "lush@demo.com": [
        {
            "title": "Lush Cosmetics Fresh Bath & Body Surplus — Bath Bombs & Soaps",
            "category": "Beauty & Personal Care",
            "quantity": 400,
            "price": 5.00,
            "condition": "new",
            "expiry_date": _exp(90),
            "description": "Surplus Lush Cosmetics fresh handmade beauty and bath products — bath bombs, shampoo bars, face masks, and artisan soaps. Natural women's beauty and personal care from Boston store overstock. Ideal for nonprofits and beauty resellers.",
            "location": "Boston, MA",
        },
    ],

    "zara@demo.com": [
        {
            "title": "Zara Women's Fashion Surplus — Dresses, Blazers & Tops",
            "category": "Women's Clothing",
            "quantity": 350,
            "price": 12.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Zara women's fashion and clothing — dresses, blazers, structured tops, and trousers from end-of-season clearance. New with tags. Women's designer-adjacent clothing ideal for resellers, thrift stores, and nonprofits providing professional attire.",
            "location": "Boston, MA",
        },
        {
            "title": "Zara Women's Accessories — Handbags, Scarves & Jewelry",
            "category": "Women's Accessories",
            "quantity": 200,
            "price": 8.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Zara women's fashion accessories — structured handbags, silk scarves, statement jewelry, and belts. Women's accessories from seasonal inventory clearance. Perfect for resellers, nonprofits supporting women, and thrift organizations.",
            "location": "Boston, MA",
        },
    ],

    "urbanoutfitters@demo.com": [
        {
            "title": "Urban Outfitters Women's Trendy Clothing Surplus",
            "category": "Women's Clothing",
            "quantity": 300,
            "price": 10.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus women's trendy clothing from Urban Outfitters Boston — vintage-inspired dresses, oversized denim, crop tops, and boho-style clothing. New with tags. Women's fashion and clothing for resellers, thrift stores, and nonprofits.",
            "location": "Boston, MA",
        },
        {
            "title": "Urban Outfitters Women's Accessories & Beauty",
            "category": "Women's Accessories",
            "quantity": 200,
            "price": 6.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus women's accessories and beauty items from Urban Outfitters Boston — hair accessories, jewelry, sunglasses, and mini beauty sets. Women's fashion accessories from seasonal clearance. Great for resellers and nonprofits.",
            "location": "Boston, MA",
        },
    ],

    "freepeople@demo.com": [
        {
            "title": "Free People Women's Boho Clothing Surplus — Dresses & Tops",
            "category": "Women's Clothing",
            "quantity": 200,
            "price": 18.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Free People women's bohemian clothing — flowy dresses, embroidered blouses, and linen tops from Boston store end-of-season clearance. New with tags. Women's fashion clothing ideal for resellers and nonprofits providing professional or transitional attire.",
            "location": "Boston, MA",
        },
    ],

    "express@demo.com": [
        {
            "title": "Express Women's Professional Clothing Surplus — Blazers & Pants",
            "category": "Women's Clothing",
            "quantity": 250,
            "price": 10.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Express women's professional and business clothing — blazers, Editor pants, and suiting separates. New with tags. Women's professional clothing ideal for nonprofits offering career attire programs, resellers, and thrift stores.",
            "location": "Boston, MA",
        },
    ],

    "bananarepublic@demo.com": [
        {
            "title": "Banana Republic Women's Business Attire Surplus",
            "category": "Women's Clothing",
            "quantity": 200,
            "price": 15.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Banana Republic women's business attire — tailored blazers, ponte pants, sheath dresses, and blouses. New with tags. Premium women's professional clothing perfect for Dress for Success programs, resellers, and nonprofits.",
            "location": "Boston, MA",
        },
        {
            "title": "Banana Republic Women's Accessories — Handbags & Scarves",
            "category": "Women's Accessories",
            "quantity": 100,
            "price": 12.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Banana Republic women's leather handbags, structured totes, and silk scarves from seasonal clearance. Premium women's accessories suitable for resellers, nonprofits providing career attire, and thrift boutiques.",
            "location": "Boston, MA",
        },
    ],

    "gap@demo.com": [
        {
            "title": "Gap Women's Essential Clothing Surplus — Denim, Tees & Fleece",
            "category": "Women's Clothing",
            "quantity": 400,
            "price": 8.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Gap women's essential clothing — denim jeans, graphic tees, hoodies, and fleece jackets from seasonal clearance. New with tags. Classic women's clothing ideal for nonprofits, shelters, and resellers.",
            "location": "Boston, MA",
        },
    ],

    "forever21@demo.com": [
        {
            "title": "Forever 21 Women's Fashion Clothing Surplus — Mixed Styles",
            "category": "Women's Clothing",
            "quantity": 500,
            "price": 5.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Forever 21 women's trendy clothing — dresses, tops, skirts, and accessories from inventory clearance. New with tags. Affordable women's fashion clothing suitable for nonprofits, resellers, and thrift organizations.",
            "location": "Boston, MA",
        },
        {
            "title": "Forever 21 Women's Jewelry & Accessories Surplus",
            "category": "Women's Accessories",
            "quantity": 400,
            "price": 3.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Forever 21 women's fashion jewelry and accessories — statement necklaces, earrings, hair accessories, and sunglasses. Women's fashion accessories from seasonal overstock. Ideal for nonprofits, resellers, and beauty programs.",
            "location": "Boston, MA",
        },
    ],

    "bcbg@demo.com": [
        {
            "title": "BCBG Max Azria Women's Designer Clothing Surplus",
            "category": "Women's Clothing",
            "quantity": 150,
            "price": 20.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus BCBG Max Azria women's designer clothing — cocktail dresses, jumpsuits, and structured blazers from end-of-season clearance. New with tags. Women's high-end fashion ideal for upscale resellers and nonprofits with dress programs.",
            "location": "Boston, MA",
        },
    ],

    "cvs@demo.com": [
        {
            "title": "Surplus CVS Health & Wellness Products — First Aid & Personal Care",
            "category": "Health & Wellness",
            "quantity": 300,
            "price": 4.00,
            "condition": "good",
            "expiry_date": _exp(180),
            "description": "Surplus health and wellness products from CVS Boston-area stores — first aid kits, personal care essentials, and OTC items. Sealed and unexpired. Ideal for shelters, food banks, and community health organizations.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus CVS Beauty & Makeup — Drugstore Cosmetics",
            "category": "Makeup & Cosmetics",
            "quantity": 400,
            "price": 5.00,
            "condition": "good",
            "expiry_date": _exp(180),
            "description": "Surplus beauty and makeup products from CVS Boston stores — mixed drugstore cosmetics including lipstick, mascara, foundation, and nail polish. Women's beauty and makeup from label change overstock. Ideal for nonprofits and resellers.",
            "location": "Boston, MA",
        },
    ],

    "staples@demo.com": [
        {
            "title": "Surplus Staples Office Supplies — Pens, Paper & Binders",
            "category": "Office Supplies",
            "quantity": 400,
            "price": 3.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus office supplies from Staples Boston-area stores — pens, paper, folders, binders, and sticky notes. New in packaging. Ideal for nonprofits, SMBs, and community organizations.",
            "location": "Framingham, MA",
        },
        {
            "title": "Surplus Staples Electronics & Tech Accessories",
            "category": "Electronics",
            "quantity": 150,
            "price": 20.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus electronics from Staples overstock — USB drives, cables, keyboards, and webcams. New in box. Ideal for nonprofits, SMBs, and tech resellers.",
            "location": "Framingham, MA",
        },
    ],

    "bose@demo.com": [
        {
            "title": "Surplus Bose Headphones — Discontinued Line, Factory New",
            "category": "Electronics",
            "quantity": 100,
            "price": 40.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Bose headphones from Framingham HQ — new units from product line transitions. Original packaging. Ideal for electronics resellers and SMB procurement.",
            "location": "Framingham, MA",
        },
    ],

    # ── MEN'S CLOTHING & ATHLETIC BRANDS ──────────────────────────────────────

    "nike@demo.com": [
        {
            "title": "Surplus Nike Men's Athletic Shirts & Shorts — Dri-FIT Training Gear",
            "category": "Men's Athletic Apparel",
            "quantity": 400,
            "price": 12.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Nike men's athletic training shirts and shorts from Boston store seasonal clearance — Dri-FIT moisture-wicking men's workout clothing in various sizes. Men's athletic apparel and sports gear suitable for nonprofits, gyms, and resellers.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus Nike Men's Running Shoes — Discontinued Styles",
            "category": "Men's Footwear",
            "quantity": 200,
            "price": 35.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Nike men's running and training shoes from Boston flagship — discontinued colorways and outgoing styles. Factory new in original boxes. Men's sneakers and athletic footwear perfect for resellers and shelter shoe programs.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus Nike Men's Hoodies & Sweatpants — Fleece Sets",
            "category": "Men's Clothing",
            "quantity": 300,
            "price": 18.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Nike men's fleece hoodies and sweatpants from seasonal overstock — club fleece crew necks, zip-up hoodies, and jogger pants. Men's casual athletic clothing and loungewear. New with tags — ideal for shelters and resellers.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus Nike Men's Jackets — Windrunner & Training",
            "category": "Men's Outerwear",
            "quantity": 150,
            "price": 25.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Nike men's jackets and outerwear from inventory transitions — Windrunner, tech fleece, and training jackets. Men's athletic outerwear suitable for resellers, shelters, and sports nonprofits.",
            "location": "Boston, MA",
        },
    ],

    "adidas@demo.com": [
        {
            "title": "Surplus Adidas Men's Athletic Clothing — Training Sets",
            "category": "Men's Athletic Apparel",
            "quantity": 350,
            "price": 10.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Adidas men's athletic training clothing — t-shirts, shorts, and track pants from seasonal clearance. Men's workout and athletic apparel featuring moisture-wicking fabric. Ideal for resellers, shelters, and athletic nonprofits.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus Adidas Men's Sneakers — Stan Smith & Campus Styles",
            "category": "Men's Footwear",
            "quantity": 180,
            "price": 30.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Adidas men's classic sneakers — Stan Smith, Campus, and Gazelle styles from outgoing inventory. New in original boxes. Men's casual footwear and sneakers great for resellers and shoe donation programs.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus Adidas Men's Soccer & Sports Gear",
            "category": "Men's Athletic Apparel",
            "quantity": 250,
            "price": 8.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Adidas men's soccer jerseys, shorts, and sports accessories — team kits and performance apparel from overstock. Men's team sports clothing ideal for youth programs, sports nonprofits, and resellers.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus Adidas Men's Hoodies & Track Jackets",
            "category": "Men's Clothing",
            "quantity": 200,
            "price": 14.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Adidas men's hoodies and track jackets from Boston inventory clearance — classic 3-stripe designs in various colorways. Men's casual athletic clothing suitable for resellers and nonprofit clothing programs.",
            "location": "Boston, MA",
        },
    ],

    "underarmour@demo.com": [
        {
            "title": "Surplus Under Armour Men's Compression Shirts & Shorts",
            "category": "Men's Athletic Apparel",
            "quantity": 300,
            "price": 10.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Under Armour men's compression athletic wear — HeatGear shirts, shorts, and leggings from overstock. Men's performance workout clothing and athletic gear ideal for gyms, resellers, and athletic programs.",
            "location": "Baltimore, MD (Boston distribution)",
        },
        {
            "title": "Surplus Under Armour Men's Training Shoes & Cleats",
            "category": "Men's Footwear",
            "quantity": 120,
            "price": 28.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Under Armour men's training shoes and athletic cleats from discontinued lines — factory new in boxes. Men's athletic footwear and sports shoes for resellers and sports equipment programs.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus Under Armour Men's Hoodies & Fleece",
            "category": "Men's Clothing",
            "quantity": 220,
            "price": 15.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Under Armour men's fleece hoodies, zip-ups, and training jackets from seasonal clearance. Men's athletic clothing and outerwear. New with tags — suitable for shelters and resellers.",
            "location": "Boston, MA",
        },
    ],

    "levis@demo.com": [
        {
            "title": "Surplus Levi's Men's Denim Jeans — 501, 511 & 513 Styles",
            "category": "Men's Clothing",
            "quantity": 400,
            "price": 15.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Levi's men's denim jeans from Boston retail overstock — classic 501 straight, 511 slim, and 513 slim straight styles in various washes and sizes. Men's jeans and denim clothing new with tags. Great for resellers and shelters.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus Levi's Men's Casual Shirts & Tops — Flannel & Denim",
            "category": "Men's Clothing",
            "quantity": 250,
            "price": 10.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Levi's men's casual shirts from seasonal clearance — flannel shirts, denim shirts, and graphic tees. Men's casual clothing and tops new with tags. Ideal for resellers, nonprofits, and shelter clothing programs.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus Levi's Men's Trucker Jackets & Outerwear",
            "category": "Men's Outerwear",
            "quantity": 150,
            "price": 20.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Levi's men's iconic trucker jackets and sherpa-lined denim jackets from inventory clearance. Men's casual outerwear new with tags. Great for resellers and community clothing programs.",
            "location": "Boston, MA",
        },
    ],

    "ralphlauren@demo.com": [
        {
            "title": "Surplus Ralph Lauren Men's Polo Shirts — Classic Fit",
            "category": "Men's Clothing",
            "quantity": 300,
            "price": 18.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Ralph Lauren men's classic polo shirts from Boston store seasonal clearance — cotton pique polo in assorted colors and sizes. Men's casual and business casual clothing new with tags. Ideal for upscale resellers and dress-for-success programs.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus Ralph Lauren Men's Chinos & Dress Pants",
            "category": "Men's Clothing",
            "quantity": 200,
            "price": 20.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Ralph Lauren men's chino pants and dress trousers from inventory transitions — slim fit and classic fit in khaki, navy, and grey. Men's business casual and dress clothing ideal for resellers and professional development programs.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus Polo Ralph Lauren Men's Sweaters & Knitwear",
            "category": "Men's Clothing",
            "quantity": 180,
            "price": 22.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Ralph Lauren men's sweaters and knitwear from seasonal overstock — cable-knit crew necks, quarter-zip pullovers, and V-neck sweaters. Men's classic clothing and knitwear ideal for resellers.",
            "location": "Boston, MA",
        },
    ],

    "tommyhilfiger@demo.com": [
        {
            "title": "Surplus Tommy Hilfiger Men's Casual Shirts & Polos",
            "category": "Men's Clothing",
            "quantity": 280,
            "price": 14.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Tommy Hilfiger men's casual shirts and polo shirts from seasonal clearance — classic-fit polos, plaid shirts, and Oxford button-downs. Men's preppy clothing and tops new with tags. Great for resellers.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus Tommy Hilfiger Men's Jeans & Chinos",
            "category": "Men's Clothing",
            "quantity": 200,
            "price": 16.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Tommy Hilfiger men's denim jeans and chino pants from inventory clearance — straight fit and slim fit in classic washes. Men's casual clothing ideal for resellers and nonprofit clothing programs.",
            "location": "Boston, MA",
        },
    ],

    "calvinklein@demo.com": [
        {
            "title": "Surplus Calvin Klein Men's Underwear & Basics — Multi-Packs",
            "category": "Men's Underwear & Basics",
            "quantity": 500,
            "price": 8.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Calvin Klein men's cotton underwear multi-packs and basics from overstock — boxer briefs, crew-neck tees, and undershirts. Men's essential clothing and underwear new in packaging. Ideal for shelters and nonprofit clothing programs.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus Calvin Klein Men's Jeans — Slim & Skinny Fit",
            "category": "Men's Clothing",
            "quantity": 250,
            "price": 18.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Calvin Klein men's jeans from seasonal inventory clearance — slim-fit and skinny-fit denim in various washes. Men's jeans and denim clothing new with tags. Great for resellers and upscale thrift programs.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus Calvin Klein Men's Dress Shirts — Cotton & Stretch",
            "category": "Men's Clothing",
            "quantity": 180,
            "price": 15.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Calvin Klein men's dress shirts from inventory transitions — slim-fit cotton and stretch dress shirts in white, blue, and grey. Men's professional clothing for dress-for-success programs and resellers.",
            "location": "Boston, MA",
        },
    ],

    "americaneagle@demo.com": [
        {
            "title": "Surplus American Eagle Men's Jeans — AirFlex & Slim",
            "category": "Men's Clothing",
            "quantity": 350,
            "price": 12.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus American Eagle men's denim jeans from seasonal clearance — AirFlex+ slim and skinny jeans in various washes and sizes. Men's jeans and casual clothing new with tags. Ideal for resellers and youth clothing programs.",
            "location": "Pittsburgh, PA (Boston distribution)",
        },
        {
            "title": "Surplus American Eagle Men's Hoodies & Graphic Tees",
            "category": "Men's Clothing",
            "quantity": 400,
            "price": 8.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus American Eagle men's casual clothing from Boston overstock — fleece hoodies, crewneck sweatshirts, and graphic tees. Men's casual apparel new with tags. Perfect for resellers, shelters, and youth programs.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus American Eagle Men's Shorts & Swim",
            "category": "Men's Clothing",
            "quantity": 250,
            "price": 7.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus American Eagle men's shorts and swim trunks from seasonal overstock — 7-inch flex shorts, jogger shorts, and board shorts. Men's summer clothing new with tags. Great for shelters and resellers.",
            "location": "Boston, MA",
        },
    ],

    "jcrew@demo.com": [
        {
            "title": "Surplus J.Crew Men's Oxford Shirts & Button-Downs",
            "category": "Men's Clothing",
            "quantity": 200,
            "price": 16.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus J.Crew men's classic Oxford shirts and button-down shirts from Boston store clearance — slim-fit and straight-fit in solid colors and plaids. Men's business casual clothing new with tags. Ideal for resellers and professional programs.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus J.Crew Men's Chinos & Stretch Pants",
            "category": "Men's Clothing",
            "quantity": 180,
            "price": 18.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus J.Crew men's chinos and stretch dress pants from inventory transitions — slim-fit straight-leg in khaki, olive, and navy. Men's business casual clothing ideal for resellers and dress-for-success programs.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus J.Crew Men's Crewneck Sweaters & Fleece",
            "category": "Men's Clothing",
            "quantity": 150,
            "price": 20.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus J.Crew men's classic crewneck sweaters and fleece pullovers from seasonal clearance. Men's knitwear and outerwear new with tags. Great for resellers and nonprofit clothing programs.",
            "location": "Boston, MA",
        },
    ],

    "carhartt@demo.com": [
        {
            "title": "Surplus Carhartt Men's Work Jackets & Coats — Duck Canvas",
            "category": "Men's Outerwear",
            "quantity": 200,
            "price": 30.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Carhartt men's workwear jackets from inventory transitions — duck canvas active jac, Detroit jacket, and sherpa-lined coats. Men's durable work outerwear new with tags. Ideal for labor nonprofits, shelters, and resellers.",
            "location": "Dearborn, MI (Boston distribution)",
        },
        {
            "title": "Surplus Carhartt Men's Pants & Bibs — Work Wear",
            "category": "Men's Clothing",
            "quantity": 250,
            "price": 18.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Carhartt men's work pants and dungaree bib overalls — relaxed-fit duck canvas and ripstop pants. Men's durable workwear clothing new with tags. Perfect for shelters, labor support programs, and resellers.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus Carhartt Men's T-Shirts & Thermal Underwear",
            "category": "Men's Clothing",
            "quantity": 400,
            "price": 8.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Carhartt men's workwear t-shirts and thermal undershirts from overstock — heavyweight cotton tees and waffle thermal long-sleeve shirts. Men's essential workwear clothing new with tags. Ideal for shelters and labor nonprofits.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus Carhartt Men's Boots & Work Footwear",
            "category": "Men's Footwear",
            "quantity": 100,
            "price": 40.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Carhartt men's work boots from discontinued lines — steel-toe and soft-toe waterproof work boots in various sizes. New in boxes. Men's durable footwear ideal for workforce development programs and resellers.",
            "location": "Boston, MA",
        },
    ],

    "patagonia@demo.com": [
        {
            "title": "Surplus Patagonia Men's Fleece Jackets — Synchilla & Better Sweater",
            "category": "Men's Outerwear",
            "quantity": 150,
            "price": 35.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Patagonia men's fleece outerwear from Boston store seasonal transitions — Synchilla Snap-T and Better Sweater fleece jackets in various colors. Men's premium outdoor clothing new with tags. Great for resellers and outdoor nonprofits.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus Patagonia Men's Down Jackets & Vests",
            "category": "Men's Outerwear",
            "quantity": 100,
            "price": 45.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Patagonia men's down-filled jackets and vests from inventory overstock — lightweight down sweater jackets and puffer vests. Men's insulated outerwear new with tags. Ideal for shelters, outdoor programs, and resellers.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus Patagonia Men's Baggies Shorts & Hiking Pants",
            "category": "Men's Athletic Apparel",
            "quantity": 200,
            "price": 20.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Patagonia men's outdoor clothing — Baggies shorts, hiking pants, and trail running shorts from seasonal clearance. Men's outdoor athletic apparel new with tags. Ideal for outdoor recreation nonprofits and resellers.",
            "location": "Boston, MA",
        },
    ],

    "northface@demo.com": [
        {
            "title": "Surplus The North Face Men's Winter Jackets — McMurdo & Nuptse",
            "category": "Men's Outerwear",
            "quantity": 120,
            "price": 50.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus The North Face men's winter jackets from Boston inventory clearance — McMurdo parka, Nuptse puffer, and Gotham jacket styles. Men's insulated winter outerwear new with tags. Ideal for shelters, winter relief programs, and resellers.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus The North Face Men's Fleece & Thermal Jackets",
            "category": "Men's Outerwear",
            "quantity": 180,
            "price": 30.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus The North Face men's mid-layer fleece — Denali fleece jackets, Gordon Lyons hoodies, and Canyonlands half-zip pullovers. Men's layering outerwear new with tags. Great for resellers and cold-weather clothing programs.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus The North Face Men's Rain Jackets & Windbreakers",
            "category": "Men's Outerwear",
            "quantity": 150,
            "price": 35.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus The North Face men's waterproof rain jackets and windbreakers from seasonal overstock — Venture 2 and Resolve rain jackets. Men's weather-resistant outerwear new with tags. Ideal for outdoor programs and resellers.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus The North Face Men's Hiking Boots & Trail Shoes",
            "category": "Men's Footwear",
            "quantity": 100,
            "price": 45.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus The North Face men's hiking boots and trail running shoes from discontinued lines — waterproof hiking boots and Hedgehog trail shoes. Men's outdoor footwear new in boxes. Ideal for outdoor nonprofits and resellers.",
            "location": "Boston, MA",
        },
    ],

    "timberland@demo.com": [
        {
            "title": "Surplus Timberland Men's Classic 6-Inch Boots",
            "category": "Men's Footwear",
            "quantity": 150,
            "price": 45.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Timberland men's iconic 6-inch waterproof boots from overstock — classic wheat nubuck and other colorways in various sizes. Men's durable footwear new in original boxes. Ideal for shelter shoe programs and resellers.",
            "location": "Stratham, NH (Boston distribution)",
        },
        {
            "title": "Surplus Timberland Men's Casual & Chukka Boots",
            "category": "Men's Footwear",
            "quantity": 120,
            "price": 35.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Timberland men's casual leather and suede boots — chukka boots and oxford styles from inventory clearance. Men's premium footwear new in original boxes. Great for resellers and professional dress programs.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus Timberland Men's Jackets & Outerwear",
            "category": "Men's Outerwear",
            "quantity": 130,
            "price": 28.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Timberland men's outerwear from seasonal clearance — waterproof field jackets, fleece hoodies, and puffer vests. Men's durable outdoor clothing new with tags. Suitable for shelters and resellers.",
            "location": "Boston, MA",
        },
    ],

    "columbia@demo.com": [
        {
            "title": "Surplus Columbia Men's Omni-Heat Winter Jackets",
            "category": "Men's Outerwear",
            "quantity": 140,
            "price": 35.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Columbia men's Omni-Heat insulated winter jackets from inventory overstock — thermal reflective lining jackets in various styles. Men's warm outerwear new with tags. Ideal for winter shelters and resellers.",
            "location": "Portland, OR (Boston distribution)",
        },
        {
            "title": "Surplus Columbia Men's Softshell & Rain Jackets",
            "category": "Men's Outerwear",
            "quantity": 170,
            "price": 25.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Columbia men's softshell and waterproof rain jackets from seasonal clearance — Watertight II and Glennaker styles. Men's weather-resistant outerwear new with tags. Great for outdoor programs and resellers.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus Columbia Men's Hiking Pants & Shorts",
            "category": "Men's Athletic Apparel",
            "quantity": 200,
            "price": 15.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Columbia men's outdoor pants and shorts from overstock — Silver Ridge convertible pants, Rapid Rivers shorts, and hiking cargo pants. Men's outdoor athletic clothing new with tags. Ideal for outdoor nonprofits and resellers.",
            "location": "Boston, MA",
        },
    ],

    "lululemonmen@demo.com": [
        {
            "title": "Surplus Lululemon Men's ABC Pants & Commission Trousers",
            "category": "Men's Athletic Apparel",
            "quantity": 200,
            "price": 30.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Lululemon men's ABC (anti-ball crushing) pants and Commission trousers from Boston store seasonal overstock — technical stretch dress and casual pants. Men's premium athletic clothing new with tags. Great for upscale resellers.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus Lululemon Men's T-Shirts & Tank Tops — Metal Vent",
            "category": "Men's Athletic Apparel",
            "quantity": 300,
            "price": 18.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Lululemon men's Metal Vent Tech shirts and Fast and Free tank tops from seasonal clearance — ultra-breathable men's workout tops. Men's premium athletic apparel new with tags. Ideal for gyms and resellers.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus Lululemon Men's Shorts — T.H.E., Pace Breaker & Surge",
            "category": "Men's Athletic Apparel",
            "quantity": 250,
            "price": 20.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Lululemon men's athletic shorts from Boston overstock — T.H.E. liner shorts, Pace Breaker 9-inch, and Surge shorts. Men's premium workout shorts new with tags. Ideal for athletics programs and resellers.",
            "location": "Boston, MA",
        },
    ],

    "brooksbros@demo.com": [
        {
            "title": "Surplus Brooks Brothers Men's Dress Shirts — Non-Iron",
            "category": "Men's Clothing",
            "quantity": 200,
            "price": 22.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Brooks Brothers men's non-iron dress shirts from inventory transitions — slim-fit and regular-fit in white, blue, and stripes. Men's professional dress clothing new with tags. Ideal for dress-for-success programs and upscale resellers.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus Brooks Brothers Men's Blazers & Sport Coats",
            "category": "Men's Clothing",
            "quantity": 100,
            "price": 50.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Brooks Brothers men's blazers and sport coats from end-of-season clearance — slim-fit and traditional cut in navy, grey, and houndstooth. Men's formal and business clothing new with tags. Ideal for job-readiness programs.",
            "location": "Boston, MA",
        },
    ],

    "vineyard@demo.com": [
        {
            "title": "Surplus Vineyard Vines Men's Whale Shirts & Polos",
            "category": "Men's Clothing",
            "quantity": 220,
            "price": 16.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Vineyard Vines men's Classic Whale polo shirts and Shep shirts from Boston store clearance — preppy coastal clothing in assorted colors. Men's casual clothing new with tags. Great for upscale resellers.",
            "location": "Boston, MA",
        },
    ],

    "uniqlo@demo.com": [
        {
            "title": "Surplus Uniqlo Men's HEATTECH Thermal Underwear Sets",
            "category": "Men's Underwear & Basics",
            "quantity": 500,
            "price": 6.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Uniqlo men's HEATTECH thermal underwear from seasonal overstock — extra-warm long sleeve shirts and thermal pants. Men's insulating base layer clothing new in packaging. Essential men's clothing for shelters and cold-weather programs.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus Uniqlo Men's AIRism T-Shirts & Polos — Unisex Basics",
            "category": "Men's Clothing",
            "quantity": 400,
            "price": 5.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Uniqlo men's and unisex AIRism moisture-control t-shirts and polo shirts from Boston overstock — breathable everyday basics. Men's essential clothing new with tags. Ideal for shelters and resellers.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus Uniqlo Unisex Fleece Hoodies & Pullovers",
            "category": "Apparel",
            "quantity": 350,
            "price": 8.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Uniqlo unisex fleece zip hoodies and pullover sweatshirts from seasonal clearance — soft anti-pilling fleece in various colors. Unisex clothing for all genders new with tags. Ideal for shelters, nonprofits, and resellers.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus Uniqlo Men's Ultra Light Down Jackets",
            "category": "Men's Outerwear",
            "quantity": 200,
            "price": 20.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Uniqlo men's Ultra Light Down packable jackets from inventory overstock — lightweight insulated puffer jackets that fold into their own pocket. Men's winter clothing new with tags. Ideal for shelters and resellers.",
            "location": "Boston, MA",
        },
    ],

    "rei@demo.com": [
        {
            "title": "Surplus REI Co-op Men's Outdoor Clothing — Shirts & Shorts",
            "category": "Men's Athletic Apparel",
            "quantity": 200,
            "price": 15.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus REI Co-op men's outdoor clothing from Boston store clearance — trail shirts, UPF 50 sun shirts, and hiking shorts. Men's outdoor athletic apparel new with tags. Great for outdoor recreation nonprofits and resellers.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus REI Camping & Outdoor Gear — Mixed Lot",
            "category": "Outdoor & Sporting Goods",
            "quantity": 150,
            "price": 20.00,
            "condition": "good",
            "expiry_date": _exp(365),
            "description": "Surplus REI camping and outdoor equipment from Boston store inventory transitions — water bottles, dry bags, camp towels, and outdoor accessories. Outdoor gear suitable for adventure nonprofits and resellers.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus REI Men's Hiking Boots & Trail Shoes",
            "category": "Men's Footwear",
            "quantity": 100,
            "price": 40.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus REI men's hiking footwear from discontinued styles — waterproof hiking boots and trail running shoes from REI Co-op and partner brands. Men's outdoor footwear new in boxes. Ideal for outdoor programs and resellers.",
            "location": "Boston, MA",
        },
    ],

    "dickssporting@demo.com": [
        {
            "title": "Surplus Dick's Men's Athletic Wear — CALIA & DSG Brands",
            "category": "Men's Athletic Apparel",
            "quantity": 300,
            "price": 8.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Dick's Sporting Goods men's athletic wear from Boston store clearance — DSG men's training shorts, shirts, and leggings. Men's budget-friendly workout clothing new with tags. Ideal for gyms, shelters, and resellers.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus Dick's Men's Athletic Shoes — Multi-Brand Clearance",
            "category": "Men's Footwear",
            "quantity": 150,
            "price": 25.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus men's athletic shoes from Dick's Sporting Goods Boston — Nike, Adidas, Under Armour, and New Balance styles from seasonal clearance. Men's sports footwear new in boxes. Ideal for resellers and athletic programs.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus Dick's Sports Equipment — Fitness & Recreation",
            "category": "Outdoor & Sporting Goods",
            "quantity": 100,
            "price": 15.00,
            "condition": "good",
            "expiry_date": _exp(365),
            "description": "Surplus sports equipment from Dick's Sporting Goods Boston — resistance bands, jump ropes, water bottles, and fitness accessories. Athletic gear suitable for gyms, nonprofits, and recreation programs.",
            "location": "Boston, MA",
        },
    ],

    # ── MEN'S GROOMING ────────────────────────────────────────────────────────

    "gillette@demo.com": [
        {
            "title": "Surplus Gillette Men's Razors & Shaving Sets — Multi-Pack",
            "category": "Men's Grooming",
            "quantity": 500,
            "price": 3.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Gillette men's razors and shaving multi-packs from P&G overstock — Fusion5, Mach3, and disposable razors. Men's grooming essentials new in packaging. Critical personal care items for shelters, veterans programs, and men's nonprofits.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus Gillette Men's Shaving Gel & Cream — Sensitive & Regular",
            "category": "Men's Grooming",
            "quantity": 400,
            "price": 2.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Gillette men's shaving gel and cream from P&G overstock — Sensitive Skin, Regular, and ProGlide shave gels. Men's personal care grooming products new in packaging. Ideal for men's shelters, nonprofits, and care kits.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus Gillette Men's Deodorant & Antiperspirant — Speed Stick & Clinical",
            "category": "Men's Grooming",
            "quantity": 600,
            "price": 1.50,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Gillette men's deodorant and antiperspirant from P&G overstock — Speed Stick, Old Spice Clinical, and Pure Sport. Men's personal care grooming products new in packaging. Essential hygiene items for men's shelters and nonprofits.",
            "location": "Canton, MA",
        },
    ],

    "oldspice@demo.com": [
        {
            "title": "Surplus Old Spice Men's Body Wash & Shower Gel — Variety Pack",
            "category": "Men's Grooming",
            "quantity": 500,
            "price": 2.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Old Spice men's body wash and shower gel from P&G overstock — Swagger, Fiji, and Timber scents. Men's personal care hygiene products new in packaging. Essential grooming items for men's shelters and hygiene programs.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus Old Spice Men's Deodorant Multi-Pack",
            "category": "Men's Grooming",
            "quantity": 600,
            "price": 1.50,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Old Spice men's deodorant from P&G overstock — Original, Swagger, and Fresh scents. Men's hygiene and grooming essentials new in packaging. Ideal for men's shelters, food banks, and care kit programs.",
            "location": "Boston, MA",
        },
    ],

    "jackblack@demo.com": [
        {
            "title": "Surplus Jack Black Men's Luxury Grooming Kit — Skincare Essentials",
            "category": "Men's Grooming",
            "quantity": 150,
            "price": 12.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Jack Black men's premium grooming products from overstock — face cleanser, moisturizer, and lip balm sets. Men's luxury skincare and grooming essentials new in packaging. Ideal for upscale resellers and men's professional programs.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus Jack Black Men's Beard & Shave Products",
            "category": "Men's Grooming",
            "quantity": 200,
            "price": 8.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Jack Black men's beard care and shaving products from overstock — beard lube, post-shave cooling gel, and beard oil. Men's premium grooming and beard care products new in packaging. Great for resellers.",
            "location": "Boston, MA",
        },
    ],

    "americancrew@demo.com": [
        {
            "title": "Surplus American Crew Men's Hair Styling Products",
            "category": "Men's Grooming",
            "quantity": 300,
            "price": 5.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus American Crew men's professional hair care products from overstock — hair gel, pomade, fiber, and styling cream. Men's hair care and grooming products new in packaging. Ideal for barbershops, shelters, and resellers.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus American Crew Men's Shampoo & Conditioner",
            "category": "Men's Grooming",
            "quantity": 400,
            "price": 4.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus American Crew men's daily shampoo and conditioner from overstock — scalp treatment, fiber shampoo, and daily conditioner. Men's hair care essentials new in packaging. Ideal for men's shelters, barbershops, and hygiene programs.",
            "location": "Boston, MA",
        },
    ],

    "niveamen@demo.com": [
        {
            "title": "Surplus Nivea Men's Skincare & Face Wash — Sensitive & Energy",
            "category": "Men's Grooming",
            "quantity": 400,
            "price": 2.50,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Nivea Men skincare products from overstock — Sensitive face wash, Energy face scrub, and Q10 anti-age moisturizer. Men's affordable skincare and face care products new in packaging. Ideal for shelters, nonprofits, and resellers.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus Nivea Men's Body Lotion & Skin Care Essentials",
            "category": "Men's Grooming",
            "quantity": 500,
            "price": 2.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Nivea Men body lotion and moisture skin care products from overstock — original and sensitive formula body lotion. Men's skincare and personal care hygiene products new in packaging. Ideal for men's shelters and hygiene programs.",
            "location": "Boston, MA",
        },
    ],

    # ── MORE FOOD & BEVERAGE ───────────────────────────────────────────────────

    "starbucks@demo.com": [
        {
            "title": "Surplus Starbucks Packaged Ground Coffee & Whole Beans",
            "category": "Beverages",
            "quantity": 400,
            "price": 4.00,
            "condition": "new",
            "expiry_date": _exp(180),
            "description": "Surplus Starbucks packaged ground coffee and whole bean coffee from Boston store overstock — Pike Place, Breakfast Blend, and seasonal roasts. Premium coffee and beverages new in sealed packaging. Ideal for food banks, resellers, and café operators.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus Starbucks Bottled Frappuccinos & Cold Brew — Cases",
            "category": "Beverages",
            "quantity": 300,
            "price": 2.50,
            "condition": "good",
            "expiry_date": _exp(60),
            "description": "Surplus Starbucks bottled Frappuccinos and cold brew coffees from distribution overstock — mocha, caramel, and vanilla flavors. Ready-to-drink beverages and coffee drinks ideal for food banks, resellers, and community distribution.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus Starbucks Pastries & Bakery Items",
            "category": "Baked Goods",
            "quantity": 200,
            "price": 2.00,
            "condition": "good",
            "expiry_date": _exp(3),
            "description": "Surplus Starbucks baked goods from Boston stores — butter croissants, banana bread, cake pops, and protein boxes. Fresh food and pastries ideal for same-day food rescue, shelters, and community meal programs.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus Starbucks VIA Instant Coffee & Tea Sachets",
            "category": "Beverages",
            "quantity": 500,
            "price": 1.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Starbucks VIA instant coffee packets and Teavana tea sachets from overstock — Italian Roast, Colombia, and various tea flavors. Instant beverages new in sealed packaging. Great for food banks, shelters, and distribution programs.",
            "location": "Boston, MA",
        },
    ],

    "chipotle@demo.com": [
        {
            "title": "Surplus Chipotle Tortillas & Tortilla Chips — Bulk Supply",
            "category": "Food & Beverage",
            "quantity": 300,
            "price": 1.50,
            "condition": "good",
            "expiry_date": _exp(14),
            "description": "Surplus Chipotle flour tortillas and tortilla chips from Boston restaurant overstock — fresh-made and sealed. Bulk food and bakery items ideal for food banks, shelters, and community meal programs.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus Chipotle Ingredients — Rice, Beans & Salsas",
            "category": "Prepared Foods",
            "quantity": 200,
            "price": 2.00,
            "condition": "good",
            "expiry_date": _exp(7),
            "description": "Surplus Chipotle prepared ingredients from Boston restaurants — cilantro-lime rice, black beans, pinto beans, and house salsas. Fresh restaurant food ideal for food rescue, community kitchens, and meal programs.",
            "location": "Boston, MA",
        },
    ],

    "lacolombe@demo.com": [
        {
            "title": "Surplus La Colombe Draft Latte & Canned Coffee — Cases",
            "category": "Beverages",
            "quantity": 250,
            "price": 3.00,
            "condition": "good",
            "expiry_date": _exp(60),
            "description": "Surplus La Colombe canned Draft Latte and cold brew coffees from Boston distribution overstock — vanilla, mocha, and pure black. Premium ready-to-drink coffee beverages ideal for resellers, food banks, and café operators.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus La Colombe Whole Bean & Ground Coffee",
            "category": "Beverages",
            "quantity": 200,
            "price": 5.00,
            "condition": "new",
            "expiry_date": _exp(180),
            "description": "Surplus La Colombe artisan roasted coffee from Boston café overstock — Corsica blend, Nizza, and seasonal single-origins. Premium specialty coffee new in sealed bags. Ideal for food banks, café operators, and resellers.",
            "location": "Boston, MA",
        },
    ],

    "finagle@demo.com": [
        {
            "title": "Surplus Finagle A Bagel Fresh Bagels — Assorted Flavors",
            "category": "Baked Goods",
            "quantity": 400,
            "price": 0.75,
            "condition": "good",
            "expiry_date": _exp(3),
            "description": "Surplus fresh bagels from Finagle A Bagel Boston — assorted flavors including plain, sesame, everything, and poppy seed. Fresh baked goods ideal for food rescue, shelters, and community breakfast programs.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus Finagle Cream Cheese & Deli Spreads",
            "category": "Dairy",
            "quantity": 150,
            "price": 2.50,
            "condition": "good",
            "expiry_date": _exp(14),
            "description": "Surplus cream cheese and deli spreads from Finagle A Bagel Boston — plain, scallion, vegetable, and lox cream cheese tubs. Refrigerated dairy food ideal for food banks and shelter meal programs.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus Finagle A Bagel Cookies & Baked Pastries",
            "category": "Baked Goods",
            "quantity": 200,
            "price": 1.00,
            "condition": "good",
            "expiry_date": _exp(2),
            "description": "Surplus cookies, muffins, and pastries from Finagle A Bagel Boston bakeries — chocolate chip cookies, blueberry muffins, and cinnamon rolls. Fresh baked goods ideal for same-day food rescue and shelter programs.",
            "location": "Boston, MA",
        },
    ],

    "bostonorganics@demo.com": [
        {
            "title": "Surplus Boston Organics Mixed Organic Produce Box",
            "category": "Produce",
            "quantity": 300,
            "price": 3.00,
            "condition": "good",
            "expiry_date": _exp(7),
            "description": "Surplus organic produce from Boston Organics — mixed seasonal vegetables and fruits sourced from local New England farms. Apples, greens, root vegetables, and herbs. Certified organic food ideal for food banks, food pantries, and produce programs.",
            "location": "Dorchester, MA",
        },
        {
            "title": "Surplus Boston Organics Leafy Greens & Herbs",
            "category": "Produce",
            "quantity": 200,
            "price": 2.00,
            "condition": "good",
            "expiry_date": _exp(5),
            "description": "Surplus organic leafy greens and fresh herbs from Boston Organics — kale, spinach, arugula, and mixed herbs from local Massachusetts farms. Fresh organic produce ideal for food rescue and community meal programs.",
            "location": "Dorchester, MA",
        },
    ],

    "boloco@demo.com": [
        {
            "title": "Surplus Boloco Boston Burrito Ingredients — Bulk Prepared",
            "category": "Prepared Foods",
            "quantity": 150,
            "price": 3.00,
            "condition": "good",
            "expiry_date": _exp(2),
            "description": "Surplus Boloco restaurant ingredients from Boston locations — seasoned rice, black beans, pulled pork, and grilled chicken. Fresh prepared food ideal for same-day food rescue, community kitchens, and shelter meal programs.",
            "location": "Boston, MA",
        },
    ],

    "shakeshack@demo.com": [
        {
            "title": "Surplus Shake Shack Brioche Buns & Bakery Items",
            "category": "Baked Goods",
            "quantity": 200,
            "price": 1.00,
            "condition": "good",
            "expiry_date": _exp(2),
            "description": "Surplus brioche potato rolls and buns from Shake Shack Boston — custom-baked potato buns used for ShackBurgers. Fresh baked goods ideal for food rescue, soup kitchens, and shelter meal programs.",
            "location": "Boston, MA",
        },
    ],

    "bostonbaking@demo.com": [
        {
            "title": "Surplus Boston Baking Co. Artisan Breads — Sourdough & Rye",
            "category": "Baked Goods",
            "quantity": 300,
            "price": 2.00,
            "condition": "good",
            "expiry_date": _exp(3),
            "description": "Surplus artisan breads from Boston Baking Co. — sourdough, whole wheat, rye, and multigrain loaves. Fresh baked goods ideal for food banks, shelters, and community food programs.",
            "location": "South Boston, MA",
        },
        {
            "title": "Surplus Boston Baking Co. Cookies & Bars — Variety Packs",
            "category": "Baked Goods",
            "quantity": 400,
            "price": 1.50,
            "condition": "good",
            "expiry_date": _exp(7),
            "description": "Surplus cookies, brownies, and energy bars from Boston Baking Co. — chocolate chip, oatmeal raisin, and fudge brownies in individually wrapped portions. Baked goods ideal for food banks, vending, and community programs.",
            "location": "South Boston, MA",
        },
    ],

    # ── MORE BEAUTY & COSMETICS ────────────────────────────────────────────────

    "glossier@demo.com": [
        {
            "title": "Surplus Glossier Skincare — Boy Brow, Cloud Paint & Balm Dotcom",
            "category": "Beauty & Skincare",
            "quantity": 200,
            "price": 10.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Glossier bestseller skincare and makeup from overstock — Boy Brow, Cloud Paint blush, and Balm Dotcom lip salve. Minimalist beauty and skincare products new in packaging. Ideal for beauty resellers and nonprofits.",
            "location": "New York, NY (Boston distribution)",
        },
        {
            "title": "Surplus Glossier Serums & Moisturizers — Priming & Futuredew",
            "category": "Beauty & Skincare",
            "quantity": 150,
            "price": 15.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Glossier skincare from overstock — Priming Moisturizer, Futuredew facial oil, and Super Glow Vitamin C serum. Premium clean beauty skincare products new in packaging. Ideal for beauty resellers and upscale nonprofits.",
            "location": "Boston, MA",
        },
    ],

    "fentybeauty@demo.com": [
        {
            "title": "Surplus Fenty Beauty Foundation — Pro Filt'r Assorted Shades",
            "category": "Makeup & Cosmetics",
            "quantity": 250,
            "price": 12.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Fenty Beauty Pro Filt'r Soft Matte foundation from overstock — 40+ inclusive shade range. Full-coverage makeup foundation new in packaging. Ideal for beauty resellers, makeup programs, and nonprofits serving diverse communities.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus Fenty Beauty Lip & Eye Products — Gloss Bomb & Mascara",
            "category": "Makeup & Cosmetics",
            "quantity": 200,
            "price": 8.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Fenty Beauty lip glosses and eye makeup from overstock — Gloss Bomb Universal Lip Luminizer and Full Frontal Mascara. Makeup cosmetics new in packaging. Ideal for beauty resellers and inclusive beauty programs.",
            "location": "Boston, MA",
        },
    ],

    "nars@demo.com": [
        {
            "title": "Surplus NARS Sheer Glow Foundation & Concealers",
            "category": "Makeup & Cosmetics",
            "quantity": 150,
            "price": 18.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus NARS luxury makeup from Boston Sephora partnership overstock — Sheer Glow foundation and Radiant Creamy Concealer in assorted shades. Premium makeup and cosmetics new in packaging. Ideal for upscale beauty resellers.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus NARS Lip & Cheek Products — Orgasm Collection",
            "category": "Makeup & Cosmetics",
            "quantity": 180,
            "price": 14.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus NARS iconic lip and cheek products from overstock — Orgasm blush, lipstick, and lip gloss. Luxury makeup cosmetics new in packaging. Great for beauty resellers and upscale makeup programs.",
            "location": "Boston, MA",
        },
    ],

    "maccosmetics@demo.com": [
        {
            "title": "Surplus MAC Cosmetics Lipstick — Ruby Woo & Studio Fix",
            "category": "Makeup & Cosmetics",
            "quantity": 300,
            "price": 10.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus MAC Cosmetics professional lipsticks from Boston store clearance — Ruby Woo, Velvet Teddy, and Studio Fix shade range. Iconic makeup lipstick new in packaging. Ideal for beauty resellers and makeup donation programs.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus MAC Studio Fix Powder & Foundation",
            "category": "Makeup & Cosmetics",
            "quantity": 200,
            "price": 12.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus MAC Studio Fix Powder plus Foundation and Face & Body foundation from overstock — professional makeup formula in assorted shades. Full-coverage cosmetics new in packaging. Ideal for beauty resellers and makeup programs.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus MAC Eyeshadow Palettes & Eye Products",
            "category": "Makeup & Cosmetics",
            "quantity": 150,
            "price": 15.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus MAC professional eyeshadow palettes and eye makeup from overstock — 9-pan palettes, kajal liners, and mascara. Professional makeup cosmetics new in packaging. Ideal for beauty resellers and makeup programs.",
            "location": "Boston, MA",
        },
    ],

    "urbandecay@demo.com": [
        {
            "title": "Surplus Urban Decay Naked Eyeshadow Palettes",
            "category": "Makeup & Cosmetics",
            "quantity": 150,
            "price": 20.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Urban Decay Naked eyeshadow palettes from Boston overstock — Naked Original, Naked3, and Naked Basics. Iconic makeup palettes new in packaging. Ideal for beauty resellers and makeup donation programs.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus Urban Decay All Nighter Setting Spray & Primer",
            "category": "Beauty & Skincare",
            "quantity": 200,
            "price": 10.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Urban Decay makeup setting spray and primer from overstock — All Nighter long-lasting setting spray and eyeshadow primer. Makeup finishing and prep products new in packaging. Ideal for beauty resellers.",
            "location": "Boston, MA",
        },
    ],

    "tartecosmetics@demo.com": [
        {
            "title": "Surplus Tarte Shape Tape Concealers & Foundation",
            "category": "Makeup & Cosmetics",
            "quantity": 200,
            "price": 12.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Tarte Shape Tape concealers and Rainforest of the Sea foundation from overstock — natural, clean beauty makeup in assorted shades. Makeup cosmetics new in packaging. Ideal for beauty resellers and clean beauty programs.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus Tarte Lip Products & Blush — Amazonian Clay",
            "category": "Makeup & Cosmetics",
            "quantity": 180,
            "price": 8.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Tarte natural lip products and Amazonian clay blush from overstock — maracuja lip gloss, Lippie Smudge and blush palettes. Clean beauty makeup cosmetics new in packaging. Great for beauty resellers.",
            "location": "Boston, MA",
        },
    ],

    "toofaced@demo.com": [
        {
            "title": "Surplus Too Faced Better Than Sex Mascara — Multi-Pack",
            "category": "Makeup & Cosmetics",
            "quantity": 250,
            "price": 10.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Too Faced Better Than Sex mascara from overstock — full-size and travel size makeup mascara. Bestselling eye makeup cosmetics new in packaging. Ideal for beauty resellers and makeup programs.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus Too Faced Palettes & Eyeshadow",
            "category": "Makeup & Cosmetics",
            "quantity": 180,
            "price": 15.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Too Faced eyeshadow palettes from seasonal overstock — Natural Eyes, Sweet Peach, and Born This Way. Makeup eye palettes new in packaging. Ideal for beauty resellers.",
            "location": "Boston, MA",
        },
    ],

    "benefit@demo.com": [
        {
            "title": "Surplus Benefit Cosmetics Brow Products — Gimme Brow & 24-Hour",
            "category": "Makeup & Cosmetics",
            "quantity": 220,
            "price": 8.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Benefit Cosmetics brow products from Boston Sephora overstock — Gimme Brow volumizing gel, 24-Hour Brow Setter, and Ka-Brow cream. Iconic makeup brow products new in packaging. Ideal for beauty resellers.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus Benefit They're Real Mascara & Eyeliner",
            "category": "Makeup & Cosmetics",
            "quantity": 200,
            "price": 10.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Benefit They're Real mascara and precision eyeliner from overstock — bestselling eye makeup and liner. Makeup cosmetics new in packaging. Great for beauty resellers and makeup programs.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus Benefit Cheek Products — Hoola Bronzer & Dandelion Blush",
            "category": "Makeup & Cosmetics",
            "quantity": 170,
            "price": 12.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Benefit Cosmetics face makeup from overstock — Hoola matte bronzer, Dandelion powder blush, and Benetint cheek stain. Bestselling makeup and cosmetics new in packaging. Ideal for beauty resellers.",
            "location": "Boston, MA",
        },
    ],

    # ── HOME GOODS ────────────────────────────────────────────────────────────

    "cratebarrel@demo.com": [
        {
            "title": "Surplus Crate & Barrel Kitchenware — Pots, Pans & Bakeware",
            "category": "Home Goods",
            "quantity": 150,
            "price": 20.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Crate & Barrel kitchenware from Boston store clearance — nonstick cookware, ceramic bakeware, and kitchen accessories. Home goods and kitchen essentials new in original packaging. Ideal for shelters, resellers, and community programs.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus Crate & Barrel Tableware & Serveware — Mixed Lots",
            "category": "Home Goods",
            "quantity": 200,
            "price": 10.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Crate & Barrel tableware from inventory overstock — dinnerware sets, bowls, serving platters, and glassware. Home goods suitable for shelters, community organizations, and resellers.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus Crate & Barrel Bedding & Bath — Towels & Linens",
            "category": "Home Goods",
            "quantity": 300,
            "price": 12.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Crate & Barrel bedding and bath items from seasonal clearance — cotton towel sets, bath mats, and bed sheets. Home goods and household linens new in packaging. Ideal for shelters, transitional housing, and resellers.",
            "location": "Boston, MA",
        },
    ],

    "westelm@demo.com": [
        {
            "title": "Surplus West Elm Home Décor — Pillows, Throws & Candles",
            "category": "Home Goods",
            "quantity": 200,
            "price": 15.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus West Elm home décor from Boston store clearance — decorative pillows, throw blankets, and soy candles. Home goods and accessories new in packaging. Ideal for housing nonprofits, resellers, and community organizations.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus West Elm Kitchen & Dining Accessories",
            "category": "Home Goods",
            "quantity": 150,
            "price": 12.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus West Elm kitchen and dining accessories from inventory overstock — serving boards, kitchen textiles, and barware. Home goods new in original packaging. Ideal for shelters and resellers.",
            "location": "Boston, MA",
        },
    ],

    "potterybarn@demo.com": [
        {
            "title": "Surplus Pottery Barn Bath Towels & Bedding Essentials",
            "category": "Home Goods",
            "quantity": 250,
            "price": 15.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Pottery Barn bath and bedroom items from seasonal clearance — Hydrocotton towel sets, bath mats, and cotton duvet covers. Home goods and household linens new in packaging. Ideal for transitional housing programs and resellers.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus Pottery Barn Decorative Accessories & Gifts",
            "category": "Home Goods",
            "quantity": 180,
            "price": 18.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Pottery Barn home accessories and gift items from seasonal overstock — frames, decorative storage, and gift sets. Home goods new in original packaging. Great for resellers and community organizations.",
            "location": "Boston, MA",
        },
    ],

    "athleta@demo.com": [
        {
            "title": "Surplus Athleta Women's Leggings & Yoga Pants",
            "category": "Women's Athletic Apparel",
            "quantity": 300,
            "price": 18.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Athleta women's performance leggings and yoga pants from seasonal clearance — Chaturanga, Salutation, and Metro 7/8 styles. Women's premium activewear new with tags. Ideal for women's shelters, resellers, and athletic nonprofits.",
            "location": "Boston, MA",
        },
        {
            "title": "Surplus Athleta Women's Sports Bras & Tanks",
            "category": "Women's Athletic Apparel",
            "quantity": 250,
            "price": 12.00,
            "condition": "new",
            "expiry_date": _exp(365),
            "description": "Surplus Athleta women's sports bras and workout tank tops from Boston store overstock — various support levels and styles. Women's athletic clothing and activewear new with tags. Great for women's nonprofits and resellers.",
            "location": "Boston, MA",
        },
    ],
}


# ── Buyers ─────────────────────────────────────────────────────────────────────

BUYERS: list[dict] = [
    # ── Demo account (used by the frontend UI) ─────────────────────────────────
    {
        "email": "demo@surplusconnect.com",
        "name": "Surplus Connect Demo",
        "segment": "nonprofit",
        "profile": {
            "segment": "nonprofit",
            "preferences": ["Food & Beverage", "Makeup & Cosmetics", "Women's Clothing", "Baked Goods", "Produce"],
            "budget_min": 0.0,
            "budget_max": 0.0,
            "location": "Boston, MA",
            "notes": "Demo account for Surplus Connect platform. Matches food, beauty, makeup, clothing, and accessories.",
        },
    },

    # ── Food-focused Nonprofits ────────────────────────────────────────────────
    {
        "email": "gbfb@demo.com",
        "name": "Greater Boston Food Bank",
        "segment": "nonprofit",
        "profile": {
            "segment": "nonprofit",
            "preferences": ["Produce", "Canned Goods", "Packaged Groceries", "Bulk Dry Goods", "Dairy", "Food & Beverage", "Prepared Foods", "Baked Goods"],
            "budget_min": 0.0,
            "budget_max": 0.0,
            "location": "Boston, MA",
            "notes": "Largest hunger-relief organization in New England. Distributes food to 190 partner agencies across Eastern Massachusetts. All food categories accepted — produce, canned goods, baked goods, prepared foods, and beverages.",
        },
    },
    {
        "email": "spoonfuls@demo.com",
        "name": "Spoonfuls",
        "segment": "nonprofit",
        "profile": {
            "segment": "nonprofit",
            "preferences": ["Food & Beverage", "Produce", "Canned Goods", "Packaged Groceries", "Dairy", "Prepared Foods", "Baked Goods"],
            "budget_min": 0.0,
            "budget_max": 0.0,
            "location": "Somerville, MA",
            "notes": "Rescues surplus food from grocery stores, restaurants, and institutions to redirect to hunger-relief agencies across Greater Boston. Accepts all fresh and packaged food.",
        },
    },
    {
        "email": "foodforfree@demo.com",
        "name": "Food For Free",
        "segment": "nonprofit",
        "profile": {
            "segment": "nonprofit",
            "preferences": ["Produce", "Canned Goods", "Dairy", "Packaged Groceries", "Bulk Dry Goods", "Prepared Foods"],
            "budget_min": 0.0,
            "budget_max": 0.0,
            "location": "Cambridge, MA",
            "notes": "Provides free food to low-income individuals and families in Cambridge and Greater Boston. Focus on nutritious food staples including fresh produce, dairy, and non-perishables.",
        },
    },
    {
        "email": "abcd@demo.com",
        "name": "ABCD Food Access",
        "segment": "nonprofit",
        "profile": {
            "segment": "nonprofit",
            "preferences": ["Produce", "Packaged Groceries", "Canned Goods", "Dairy", "Food & Beverage", "Bulk Dry Goods"],
            "budget_min": 0.0,
            "budget_max": 0.0,
            "location": "Boston, MA",
            "notes": "Action for Boston Community Development — provides emergency food assistance and nutrition support to low-income Boston residents. Needs all food categories.",
        },
    },
    {
        "email": "bostonrescuemission@demo.com",
        "name": "Boston Rescue Mission",
        "segment": "nonprofit",
        "profile": {
            "segment": "nonprofit",
            "preferences": ["Prepared Foods", "Food & Beverage", "Baked Goods", "Packaged Groceries", "Canned Goods"],
            "budget_min": 0.0,
            "budget_max": 0.0,
            "location": "Boston, MA",
            "notes": "Provides meals and shelter to homeless men and women in Boston. Needs prepared food, baked goods, and packaged groceries for daily meal service. All food donations accepted.",
        },
    },
    {
        "email": "bostonhalf@demo.com",
        "name": "Project Bread",
        "segment": "nonprofit",
        "profile": {
            "segment": "nonprofit",
            "preferences": ["Baked Goods", "Packaged Groceries", "Bulk Dry Goods", "Food & Beverage", "Produce"],
            "budget_min": 0.0,
            "budget_max": 0.0,
            "location": "Boston, MA",
            "notes": "Massachusetts statewide hunger-relief organization. Connects surplus food with partner food pantries and soup kitchens across the state. Baked goods, dry goods, and produce always needed.",
        },
    },

    # ── Women's Services Nonprofits ────────────────────────────────────────────
    {
        "email": "givenglow@demo.com",
        "name": "Give n Glow",
        "segment": "nonprofit",
        "profile": {
            "segment": "nonprofit",
            "preferences": ["Makeup & Cosmetics", "Women's Accessories", "Beauty & Skincare", "Beauty & Accessories", "Women's Clothing", "Health & Wellness"],
            "budget_min": 0.0,
            "budget_max": 0.0,
            "location": "Boston, MA",
            "notes": "Nonprofit providing free makeup, cosmetics, beauty products, and women's accessories to low-income women and survivors of domestic violence in the Boston area. Needs makeup, skincare, women's accessories, and beauty products at no cost.",
        },
    },
    {
        "email": "rosies@demo.com",
        "name": "Rosie's Place",
        "segment": "nonprofit",
        "profile": {
            "segment": "nonprofit",
            "preferences": ["Women's Clothing", "Women's Accessories", "Makeup & Cosmetics", "Health & Wellness", "Beauty & Skincare", "Household Essentials"],
            "budget_min": 0.0,
            "budget_max": 0.0,
            "location": "Boston, MA",
            "notes": "Sanctuary for poor and homeless women in Boston. Needs women's clothing, accessories, makeup, cosmetics, and hygiene products for residents. All women's categories accepted.",
        },
    },
    {
        "email": "stfrancis@demo.com",
        "name": "St. Francis House",
        "segment": "nonprofit",
        "profile": {
            "segment": "nonprofit",
            "preferences": ["Apparel", "Women's Clothing", "Food & Beverage", "Health & Wellness", "Household Essentials", "Makeup & Cosmetics"],
            "budget_min": 0.0,
            "budget_max": 0.0,
            "location": "Boston, MA",
            "notes": "Provides meals, shelter, and supportive services to adults experiencing homelessness in downtown Boston. Needs food, clothing, makeup, and personal care items.",
        },
    },
    {
        "email": "dressforsuccess@demo.com",
        "name": "Dress for Success Boston",
        "segment": "nonprofit",
        "profile": {
            "segment": "nonprofit",
            "preferences": ["Women's Clothing", "Women's Accessories", "Women's Footwear", "Women's Athletic Apparel"],
            "budget_min": 0.0,
            "budget_max": 0.0,
            "location": "Boston, MA",
            "notes": "Empowers women to achieve economic independence by providing professional women's clothing and career attire. Needs all women's clothing, suits, dresses, and accessories for job interviews and employment.",
        },
    },
    {
        "email": "stvincent@demo.com",
        "name": "St. Vincent de Paul Boston",
        "segment": "nonprofit",
        "profile": {
            "segment": "nonprofit",
            "preferences": ["Women's Clothing", "Apparel", "Home Goods", "Household Essentials", "Food & Beverage"],
            "budget_min": 0.0,
            "budget_max": 0.0,
            "location": "Boston, MA",
            "notes": "Provides material assistance — food, clothing, and household goods — to families in need across Massachusetts. Accepts all apparel, women's clothing, and food donations.",
        },
    },
    {
        "email": "goodwill@demo.com",
        "name": "Goodwill Boston",
        "segment": "nonprofit",
        "profile": {
            "segment": "nonprofit",
            "preferences": ["Women's Clothing", "Apparel", "Home Goods", "Women's Accessories", "Women's Footwear", "Household Essentials"],
            "budget_min": 0.0,
            "budget_max": 0.0,
            "location": "Boston, MA",
            "notes": "Collects and resells donated goods to fund job training and employment programs in Greater Boston. Strong interest in women's clothing, accessories, and home goods.",
        },
    },

    # ── Food Resellers ────────────────────────────────────────────────────────
    {
        "email": "tgtg@demo.com",
        "name": "Too Good To Go",
        "segment": "reseller",
        "profile": {
            "segment": "reseller",
            "preferences": ["Food & Beverage", "Produce", "Packaged Groceries", "Canned Goods", "Dairy", "Bulk Dry Goods", "Prepared Foods", "Baked Goods", "Beverages"],
            "budget_min": 500.0,
            "budget_max": 5000.0,
            "location": "Boston, MA",
            "notes": "App-based surplus food rescue platform. Looking for near-expiry and surplus food lots to redistribute via consumer surprise bags. All food categories at discounted rates for resale on the app.",
        },
    },
    {
        "email": "flashfood@demo.com",
        "name": "Flashfood",
        "segment": "reseller",
        "profile": {
            "segment": "reseller",
            "preferences": ["Packaged Groceries", "Canned Goods", "Produce", "Dairy", "Food & Beverage", "Bulk Dry Goods"],
            "budget_min": 1000.0,
            "budget_max": 8000.0,
            "location": "Boston, MA",
            "notes": "Grocery savings app connecting shoppers with near-expiry food items at deep discounts. Primarily interested in packaged grocery food items and produce at discounted rates.",
        },
    },
    {
        "email": "foodrescue@demo.com",
        "name": "Food Rescue US — Boston",
        "segment": "reseller",
        "profile": {
            "segment": "reseller",
            "preferences": ["Food & Beverage", "Produce", "Canned Goods", "Packaged Groceries", "Dairy", "Bulk Dry Goods", "Prepared Foods"],
            "budget_min": 0.0,
            "budget_max": 2000.0,
            "location": "Boston, MA",
            "notes": "Technology-enabled food rescue connecting donors with nonprofits. Primarily sourcing all food categories for immediate redistribution. Food at any price point considered.",
        },
    },

    # ── Fashion & Beauty Resellers ─────────────────────────────────────────────
    {
        "email": "boomerangs@demo.com",
        "name": "Boomerangs Boston",
        "segment": "reseller",
        "profile": {
            "segment": "reseller",
            "preferences": ["Women's Clothing", "Apparel", "Home Goods", "Women's Accessories", "Women's Footwear", "Makeup & Cosmetics"],
            "budget_min": 200.0,
            "budget_max": 3000.0,
            "location": "Boston, MA",
            "notes": "Upscale thrift stores benefiting AIDS Action Committee of Massachusetts. Specializes in women's clothing, accessories, and home goods for resale at discounted rates.",
        },
    },
    {
        "email": "thredup@demo.com",
        "name": "ThredUp Boston Reseller",
        "segment": "reseller",
        "profile": {
            "segment": "reseller",
            "preferences": ["Women's Clothing", "Women's Accessories", "Women's Footwear", "Apparel"],
            "budget_min": 300.0,
            "budget_max": 5000.0,
            "location": "Boston, MA",
            "notes": "Online secondhand women's fashion reseller. Looking for surplus women's clothing, accessories, and footwear in good to new condition for resale on the ThredUp platform.",
        },
    },
    {
        "email": "beautyreseller@demo.com",
        "name": "Boston Beauty Depot — Reseller",
        "segment": "reseller",
        "profile": {
            "segment": "reseller",
            "preferences": ["Makeup & Cosmetics", "Beauty & Skincare", "Beauty & Accessories", "Beauty & Hair Care", "Beauty & Personal Care"],
            "budget_min": 500.0,
            "budget_max": 6000.0,
            "location": "Boston, MA",
            "notes": "Independent beauty and cosmetics reseller sourcing surplus makeup, skincare, and beauty products at discounted rates. Specializes in reselling drugstore and mid-tier beauty brands.",
        },
    },
    {
        "email": "bostonsmb@demo.com",
        "name": "Boston Local SMB",
        "segment": "smb",
        "profile": {
            "segment": "smb",
            "preferences": ["Office Supplies", "Electronics", "Bulk Dry Goods", "Household Essentials", "Beverages"],
            "budget_min": 500.0,
            "budget_max": 4000.0,
            "location": "Boston, MA",
            "notes": "Local Boston small business seeking office supplies, electronics, and operational goods at below-retail prices.",
        },
    },

    # ── Men's Shelters & Veterans Organizations ───────────────────────────────
    {
        "email": "pinestreetinn@demo.com",
        "name": "Pine Street Inn Men's Shelter",
        "segment": "nonprofit",
        "profile": {
            "segment": "nonprofit",
            "preferences": ["Men's Clothing", "Men's Outerwear", "Men's Footwear", "Men's Underwear & Basics", "Men's Grooming", "Food & Beverage", "Baked Goods"],
            "budget_min": 0.0,
            "budget_max": 0.0,
            "location": "Boston, MA",
            "notes": "Boston's largest provider of homeless services for men. Urgently needs men's clothing, men's outerwear, men's boots, men's underwear, men's grooming products, and food for daily meal service. Men's jackets, shirts, jeans, and socks always needed.",
        },
    },
    {
        "email": "shattuckshelter@demo.com",
        "name": "Shattuck Shelter Boston",
        "segment": "nonprofit",
        "profile": {
            "segment": "nonprofit",
            "preferences": ["Men's Clothing", "Men's Grooming", "Food & Beverage", "Prepared Foods", "Men's Underwear & Basics", "Baked Goods"],
            "budget_min": 0.0,
            "budget_max": 0.0,
            "location": "Jamaica Plain, MA",
            "notes": "Men's emergency shelter at Boston's Shattuck Hospital campus. Needs men's clothing donations including men's shirts, pants, underwear, and socks, plus food for meal service. Men's personal care hygiene and grooming products also needed.",
        },
    },
    {
        "email": "veteransne@demo.com",
        "name": "Veterans Northeast Outreach Center",
        "segment": "nonprofit",
        "profile": {
            "segment": "nonprofit",
            "preferences": ["Men's Clothing", "Men's Outerwear", "Men's Footwear", "Men's Grooming", "Food & Beverage", "Men's Athletic Apparel", "Men's Underwear & Basics"],
            "budget_min": 0.0,
            "budget_max": 0.0,
            "location": "Haverhill, MA",
            "notes": "Provides services to veterans across northeastern Massachusetts. Needs men's clothing including men's dress shirts for job interviews, men's outerwear, men's boots, men's grooming supplies, and food items for veteran food pantry.",
        },
    },
    {
        "email": "newenglandstanddown@demo.com",
        "name": "New England Stand Down — Veterans Services",
        "segment": "nonprofit",
        "profile": {
            "segment": "nonprofit",
            "preferences": ["Men's Clothing", "Men's Outerwear", "Men's Footwear", "Men's Grooming", "Men's Athletic Apparel", "Food & Beverage"],
            "budget_min": 0.0,
            "budget_max": 0.0,
            "location": "Boston, MA",
            "notes": "Annual event and ongoing program serving homeless and at-risk veterans in Greater Boston. Needs new men's clothing including men's work boots, men's jackets, men's shirts, men's pants, and men's grooming kits.",
        },
    },
    {
        "email": "americanlegionma@demo.com",
        "name": "American Legion Massachusetts",
        "segment": "nonprofit",
        "profile": {
            "segment": "nonprofit",
            "preferences": ["Men's Clothing", "Men's Outerwear", "Men's Grooming", "Food & Beverage", "Beverages", "Men's Athletic Apparel"],
            "budget_min": 0.0,
            "budget_max": 500.0,
            "location": "Boston, MA",
            "notes": "Massachusetts American Legion veterans organization. Distributes clothing and supplies to veteran members in need. Men's clothing including men's outerwear, dress shirts, work boots, and men's grooming products are top needs.",
        },
    },
    {
        "email": "bostonveteranscenter@demo.com",
        "name": "Boston Veterans Center",
        "segment": "nonprofit",
        "profile": {
            "segment": "nonprofit",
            "preferences": ["Men's Clothing", "Men's Grooming", "Men's Athletic Apparel", "Men's Underwear & Basics", "Food & Beverage"],
            "budget_min": 0.0,
            "budget_max": 0.0,
            "location": "Boston, MA",
            "notes": "VA-affiliated readjustment counseling center serving veterans. Collects men's clothing, grooming products, and non-perishable food for veteran outreach programs.",
        },
    },

    # ── More Women's Shelters & Nonprofits ────────────────────────────────────
    {
        "email": "rosiesplace@demo.com",
        "name": "Rosie's Place Women's Shelter",
        "segment": "nonprofit",
        "profile": {
            "segment": "nonprofit",
            "preferences": ["Women's Clothing", "Women's Accessories", "Makeup & Cosmetics", "Beauty & Skincare", "Food & Beverage", "Baked Goods", "Produce"],
            "budget_min": 0.0,
            "budget_max": 0.0,
            "location": "Boston, MA",
            "notes": "First women's shelter in the US. Needs women's clothing donations, beauty and makeup products, women's accessories, and food for meal programs. Also accepts skincare and personal care items for women.",
        },
    },
    {
        "email": "bwfh@demo.com",
        "name": "Brigham and Women's Community Programs",
        "segment": "nonprofit",
        "profile": {
            "segment": "nonprofit",
            "preferences": ["Food & Beverage", "Produce", "Canned Goods", "Health & Wellness", "Women's Clothing", "Makeup & Cosmetics"],
            "budget_min": 0.0,
            "budget_max": 0.0,
            "location": "Boston, MA",
            "notes": "Community health programs affiliated with Brigham and Women's Hospital. Distributes food and personal care items to patients and community members in need.",
        },
    },
    {
        "email": "dfssboston@demo.com",
        "name": "Dress for Success Boston",
        "segment": "nonprofit",
        "profile": {
            "segment": "nonprofit",
            "preferences": ["Women's Clothing", "Women's Accessories", "Women's Footwear", "Makeup & Cosmetics", "Beauty & Skincare"],
            "budget_min": 0.0,
            "budget_max": 0.0,
            "location": "Boston, MA",
            "notes": "Empowers women to achieve economic independence through professional attire. Needs women's professional clothing, women's business suits and dresses, women's accessories, and makeup for job interview preparation.",
        },
    },
    {
        "email": "projectbeautyshare@demo.com",
        "name": "Project Beauty Share",
        "segment": "nonprofit",
        "profile": {
            "segment": "nonprofit",
            "preferences": ["Makeup & Cosmetics", "Beauty & Skincare", "Beauty & Hair Care", "Women's Accessories", "Men's Grooming"],
            "budget_min": 0.0,
            "budget_max": 0.0,
            "location": "Boston, MA",
            "notes": "Distributes donated beauty products to women in need across Greater Boston. Accepts all types of new and gently used beauty products — makeup, skincare, haircare, and grooming items.",
        },
    },
    {
        "email": "ywcaboston@demo.com",
        "name": "YWCA Boston",
        "segment": "nonprofit",
        "profile": {
            "segment": "nonprofit",
            "preferences": ["Women's Clothing", "Women's Athletic Apparel", "Makeup & Cosmetics", "Beauty & Skincare", "Food & Beverage", "Women's Accessories"],
            "budget_min": 0.0,
            "budget_max": 500.0,
            "location": "Boston, MA",
            "notes": "YWCA Boston empowers women through economic advancement programs. Needs women's professional clothing, women's activewear, beauty products, and food for community events and programs.",
        },
    },

    # ── Food & Hunger Relief Nonprofits ───────────────────────────────────────
    {
        "email": "faithfoodpantry@demo.com",
        "name": "Emmanuel Faith Food Pantry",
        "segment": "nonprofit",
        "profile": {
            "segment": "nonprofit",
            "preferences": ["Food & Beverage", "Canned Goods", "Produce", "Baked Goods", "Packaged Groceries", "Dairy", "Beverages"],
            "budget_min": 0.0,
            "budget_max": 0.0,
            "location": "Boston, MA",
            "notes": "Faith-based community food pantry serving South End and surrounding neighborhoods. All food categories accepted — canned goods, produce, baked goods, beverages, and packaged groceries.",
        },
    },
    {
        "email": "haitianhealth@demo.com",
        "name": "Haitian American Public Health Initiative",
        "segment": "nonprofit",
        "profile": {
            "segment": "nonprofit",
            "preferences": ["Food & Beverage", "Produce", "Canned Goods", "Packaged Groceries", "Health & Wellness"],
            "budget_min": 0.0,
            "budget_max": 0.0,
            "location": "Dorchester, MA",
            "notes": "Community health organization serving Haitian American community in Dorchester. Distributes food and health supplies to families in need.",
        },
    },
    {
        "email": "dorchesterhouse@demo.com",
        "name": "Dorchester House Community Meals",
        "segment": "nonprofit",
        "profile": {
            "segment": "nonprofit",
            "preferences": ["Prepared Foods", "Food & Beverage", "Produce", "Canned Goods", "Baked Goods"],
            "budget_min": 0.0,
            "budget_max": 0.0,
            "location": "Dorchester, MA",
            "notes": "Community health center providing meal programs and food assistance in Dorchester. Needs prepared foods, fresh produce, and packaged groceries for daily meal service.",
        },
    },
    {
        "email": "southendcomm@demo.com",
        "name": "South End Community Health Food Program",
        "segment": "nonprofit",
        "profile": {
            "segment": "nonprofit",
            "preferences": ["Food & Beverage", "Produce", "Canned Goods", "Packaged Groceries", "Dairy", "Baked Goods"],
            "budget_min": 0.0,
            "budget_max": 0.0,
            "location": "South End, Boston, MA",
            "notes": "Community health food program in the South End. Distributes food to low-income families including fresh produce, canned goods, dairy, and baked goods.",
        },
    },
    {
        "email": "horizonshomeless@demo.com",
        "name": "Horizons for Homeless Children",
        "segment": "nonprofit",
        "profile": {
            "segment": "nonprofit",
            "preferences": ["Food & Beverage", "Baked Goods", "Produce", "Apparel", "Home Goods"],
            "budget_min": 0.0,
            "budget_max": 0.0,
            "location": "Boston, MA",
            "notes": "Serves homeless children and their families across Massachusetts. Needs food for child meal programs, children's clothing, and home goods for families transitioning to housing.",
        },
    },
    {
        "email": "bostonrescuemission@demo.com",
        "name": "Boston Rescue Mission",
        "segment": "nonprofit",
        "profile": {
            "segment": "nonprofit",
            "preferences": ["Food & Beverage", "Prepared Foods", "Baked Goods", "Canned Goods", "Men's Clothing", "Men's Grooming"],
            "budget_min": 0.0,
            "budget_max": 0.0,
            "location": "Boston, MA",
            "notes": "Serves homeless men and women with meals, shelter, and recovery programs. Needs food for daily meal service, men's clothing and grooming supplies, and women's clothing.",
        },
    },
    {
        "email": "stfrancishouse@demo.com",
        "name": "St. Francis House Boston",
        "segment": "nonprofit",
        "profile": {
            "segment": "nonprofit",
            "preferences": ["Men's Clothing", "Men's Outerwear", "Men's Footwear", "Men's Grooming", "Food & Beverage", "Prepared Foods", "Beverages"],
            "budget_min": 0.0,
            "budget_max": 0.0,
            "location": "Boston, MA",
            "notes": "Day shelter serving Boston's most vulnerable. Desperately needs men's clothing including outerwear, boots, and shirts. Also needs daily food for meal service and men's grooming and hygiene products.",
        },
    },
    {
        "email": "bostoncatholiccharities@demo.com",
        "name": "Catholic Charities Boston",
        "segment": "nonprofit",
        "profile": {
            "segment": "nonprofit",
            "preferences": ["Food & Beverage", "Canned Goods", "Produce", "Baked Goods", "Men's Clothing", "Women's Clothing", "Home Goods"],
            "budget_min": 0.0,
            "budget_max": 500.0,
            "location": "Boston, MA",
            "notes": "Catholic Charities of the Archdiocese of Boston. Provides food, clothing, and home goods to families in need across Greater Boston.",
        },
    },
    {
        "email": "svdpboston@demo.com",
        "name": "Society of St. Vincent de Paul Boston",
        "segment": "nonprofit",
        "profile": {
            "segment": "nonprofit",
            "preferences": ["Food & Beverage", "Canned Goods", "Men's Clothing", "Women's Clothing", "Home Goods", "Apparel"],
            "budget_min": 0.0,
            "budget_max": 0.0,
            "location": "Boston, MA",
            "notes": "Catholic charitable organization serving the poor in Boston. Distributes food, clothing, and home goods to families in need through local conferences throughout Greater Boston.",
        },
    },

    # ── Youth Organizations ────────────────────────────────────────────────────
    {
        "email": "bgcboston@demo.com",
        "name": "Boys & Girls Club of Boston",
        "segment": "nonprofit",
        "profile": {
            "segment": "nonprofit",
            "preferences": ["Men's Athletic Apparel", "Men's Clothing", "Women's Athletic Apparel", "Food & Beverage", "Outdoor & Sporting Goods", "Apparel"],
            "budget_min": 0.0,
            "budget_max": 500.0,
            "location": "Boston, MA",
            "notes": "Youth development organization serving 13,000+ youth across Boston. Needs athletic clothing for kids and teens, sports equipment, and food for after-school programs. Boys' and men's athletic wear especially needed.",
        },
    },
    {
        "email": "cityconnects@demo.com",
        "name": "City Connects Boston",
        "segment": "nonprofit",
        "profile": {
            "segment": "nonprofit",
            "preferences": ["Food & Beverage", "Apparel", "Men's Clothing", "Women's Clothing", "Home Goods"],
            "budget_min": 0.0,
            "budget_max": 0.0,
            "location": "Boston, MA",
            "notes": "Boston school-based program connecting students to community resources. Sources clothing and food for at-risk children and their families through Boston Public Schools partnerships.",
        },
    },
    {
        "email": "bostonafter3@demo.com",
        "name": "Boston After School & Beyond",
        "segment": "nonprofit",
        "profile": {
            "segment": "nonprofit",
            "preferences": ["Food & Beverage", "Baked Goods", "Beverages", "Men's Athletic Apparel", "Women's Athletic Apparel"],
            "budget_min": 0.0,
            "budget_max": 0.0,
            "location": "Boston, MA",
            "notes": "Networks afterschool programs serving Boston youth. Needs snacks, food, and beverages for afterschool programs. Also collects athletic clothing for youth sports activities.",
        },
    },
    {
        "email": "ymcagreaterboston@demo.com",
        "name": "YMCA Greater Boston",
        "segment": "nonprofit",
        "profile": {
            "segment": "nonprofit",
            "preferences": ["Men's Athletic Apparel", "Women's Athletic Apparel", "Men's Footwear", "Food & Beverage", "Outdoor & Sporting Goods", "Men's Clothing"],
            "budget_min": 0.0,
            "budget_max": 1000.0,
            "location": "Boston, MA",
            "notes": "YMCA of Greater Boston serves all ages across multiple branches. Needs athletic clothing and gear for fitness programs, food for community events, and clothing for low-income members.",
        },
    },

    # ── Men's Fashion Resellers ───────────────────────────────────────────────
    {
        "email": "mensthrifthub@demo.com",
        "name": "Men's Thrift Hub Boston",
        "segment": "reseller",
        "profile": {
            "segment": "reseller",
            "preferences": ["Men's Clothing", "Men's Outerwear", "Men's Footwear", "Men's Athletic Apparel", "Apparel"],
            "budget_min": 200.0,
            "budget_max": 4000.0,
            "location": "Boston, MA",
            "notes": "Men's thrift reseller sourcing surplus men's clothing and footwear for resale. Specializes in men's denim jeans, men's jackets, men's boots, and men's athletic wear.",
        },
    },
    {
        "email": "vintagemenswear@demo.com",
        "name": "Boston Vintage Men's Fashion",
        "segment": "reseller",
        "profile": {
            "segment": "reseller",
            "preferences": ["Men's Clothing", "Men's Outerwear", "Men's Footwear", "Men's Athletic Apparel"],
            "budget_min": 300.0,
            "budget_max": 5000.0,
            "location": "Cambridge, MA",
            "notes": "Vintage and surplus men's fashion reseller serving the greater Boston area. Looking for men's designer and brand-name clothing including Levi's jeans, Ralph Lauren polos, Tommy Hilfiger, and men's outerwear.",
        },
    },
    {
        "email": "sneakerreseller@demo.com",
        "name": "Boston Sneaker Exchange",
        "segment": "reseller",
        "profile": {
            "segment": "reseller",
            "preferences": ["Men's Footwear", "Women's Footwear", "Men's Athletic Apparel"],
            "budget_min": 500.0,
            "budget_max": 6000.0,
            "location": "Boston, MA",
            "notes": "Sneaker and athletic footwear reseller specializing in Nike, Adidas, New Balance, and Jordan brand. Looking for surplus men's sneakers, athletic shoes, and limited edition footwear for resale.",
        },
    },
    {
        "email": "athleticreseller@demo.com",
        "name": "Boston Athletic Gear Resellers",
        "segment": "reseller",
        "profile": {
            "segment": "reseller",
            "preferences": ["Men's Athletic Apparel", "Women's Athletic Apparel", "Men's Footwear", "Outdoor & Sporting Goods"],
            "budget_min": 400.0,
            "budget_max": 5000.0,
            "location": "Boston, MA",
            "notes": "Athletic and outdoor gear reseller. Sources surplus Nike, Adidas, Under Armour, Patagonia, North Face, and Columbia clothing and footwear for discounted resale.",
        },
    },
    {
        "email": "poshmarkboston@demo.com",
        "name": "Poshmark Boston Closet",
        "segment": "reseller",
        "profile": {
            "segment": "reseller",
            "preferences": ["Men's Clothing", "Women's Clothing", "Men's Athletic Apparel", "Women's Athletic Apparel", "Men's Footwear", "Women's Footwear", "Women's Accessories"],
            "budget_min": 200.0,
            "budget_max": 3000.0,
            "location": "Boston, MA",
            "notes": "Poshmark reseller operating a mixed-gender fashion closet. Buys surplus men's and women's clothing and accessories for resale on Poshmark and Mercari. All brands welcome.",
        },
    },
    {
        "email": "depopboston@demo.com",
        "name": "Depop Boston Fashion Reseller",
        "segment": "reseller",
        "profile": {
            "segment": "reseller",
            "preferences": ["Men's Clothing", "Women's Clothing", "Men's Outerwear", "Men's Athletic Apparel", "Women's Athletic Apparel"],
            "budget_min": 100.0,
            "budget_max": 2000.0,
            "location": "Boston, MA",
            "notes": "Gen Z fashion reseller on Depop targeting streetwear and athleisure. Looking for surplus Nike, Adidas, Carhartt, Patagonia, and similar men's and women's clothing for trendy resale.",
        },
    },
    {
        "email": "outdoorgearresale@demo.com",
        "name": "Boston Outdoor Gear Resale",
        "segment": "reseller",
        "profile": {
            "segment": "reseller",
            "preferences": ["Men's Outerwear", "Men's Athletic Apparel", "Outdoor & Sporting Goods", "Men's Footwear"],
            "budget_min": 300.0,
            "budget_max": 4000.0,
            "location": "Boston, MA",
            "notes": "Outdoor and adventure gear reseller specializing in North Face, Patagonia, Columbia, REI, and Timberland surplus. Looking for men's outdoor jackets, hiking boots, and camping equipment for discounted resale.",
        },
    },
    {
        "email": "luxurymenswear@demo.com",
        "name": "Boston Luxury Men's Consignment",
        "segment": "reseller",
        "profile": {
            "segment": "reseller",
            "preferences": ["Men's Clothing", "Men's Outerwear", "Men's Footwear"],
            "budget_min": 1000.0,
            "budget_max": 8000.0,
            "location": "Boston, MA",
            "notes": "Upscale men's consignment shop in Beacon Hill. Sources surplus Ralph Lauren, Brooks Brothers, Vineyard Vines, J.Crew, and Lululemon men's clothing for consignment resale.",
        },
    },

    # ── Beauty & Cosmetics Resellers ──────────────────────────────────────────
    {
        "email": "beautyboxboston@demo.com",
        "name": "Boston BeautyBox Subscription",
        "segment": "reseller",
        "profile": {
            "segment": "reseller",
            "preferences": ["Makeup & Cosmetics", "Beauty & Skincare", "Beauty & Hair Care"],
            "budget_min": 500.0,
            "budget_max": 5000.0,
            "location": "Boston, MA",
            "notes": "Subscription beauty box company sourcing surplus makeup, skincare, and haircare for monthly subscription boxes. Needs Fenty Beauty, MAC, NARS, Urban Decay, Tarte, and similar premium and drugstore brands.",
        },
    },
    {
        "email": "blackbeautycollective@demo.com",
        "name": "Black Beauty Collective Boston",
        "segment": "reseller",
        "profile": {
            "segment": "reseller",
            "preferences": ["Makeup & Cosmetics", "Beauty & Skincare", "Women's Accessories"],
            "budget_min": 300.0,
            "budget_max": 4000.0,
            "location": "Roxbury, MA",
            "notes": "Beauty reseller and community organization serving Black women in Greater Boston. Sources diverse-shade makeup and skincare including Fenty Beauty, MAC, and NARS for affordable resale in the community.",
        },
    },
    {
        "email": "beautyoutlet@demo.com",
        "name": "Boston Beauty Outlet",
        "segment": "reseller",
        "profile": {
            "segment": "reseller",
            "preferences": ["Makeup & Cosmetics", "Beauty & Skincare", "Beauty & Hair Care", "Beauty & Personal Care"],
            "budget_min": 400.0,
            "budget_max": 6000.0,
            "location": "Boston, MA",
            "notes": "Discount beauty outlet sourcing surplus cosmetics and skincare for below-retail resale. Looking for all major makeup brands including e.l.f., NYX, Revlon, L'Oréal, Colourpop, Glossier, and MAC.",
        },
    },

    # ── Food Resellers & Distributors ─────────────────────────────────────────
    {
        "email": "freshdepot@demo.com",
        "name": "Fresh Depot Food Reseller",
        "segment": "reseller",
        "profile": {
            "segment": "reseller",
            "preferences": ["Food & Beverage", "Produce", "Canned Goods", "Packaged Groceries", "Baked Goods", "Beverages"],
            "budget_min": 500.0,
            "budget_max": 8000.0,
            "location": "Boston, MA",
            "notes": "Food distribution reseller purchasing surplus grocery and food items for wholesale redistribution. Looking for bulk food, produce, canned goods, baked goods, and beverages.",
        },
    },
    {
        "email": "urbanharvestdist@demo.com",
        "name": "Urban Harvest Food Distribution",
        "segment": "reseller",
        "profile": {
            "segment": "reseller",
            "preferences": ["Produce", "Food & Beverage", "Bulk Dry Goods", "Packaged Groceries", "Canned Goods"],
            "budget_min": 300.0,
            "budget_max": 6000.0,
            "location": "Roxbury, MA",
            "notes": "Food distribution company purchasing surplus produce and groceries at below-market prices for resale in food deserts and low-income Boston neighborhoods.",
        },
    },
    {
        "email": "cafesupplyboston@demo.com",
        "name": "Boston Café Supply Co.",
        "segment": "reseller",
        "profile": {
            "segment": "reseller",
            "preferences": ["Beverages", "Food & Beverage", "Baked Goods", "Packaged Groceries"],
            "budget_min": 500.0,
            "budget_max": 5000.0,
            "location": "Boston, MA",
            "notes": "Café supply company sourcing surplus coffee, beverages, baked goods, and packaged food for wholesale supply to Boston cafés and coffee shops.",
        },
    },
    {
        "email": "restaurantprocure@demo.com",
        "name": "Boston Restaurant Supply Procurement",
        "segment": "reseller",
        "profile": {
            "segment": "reseller",
            "preferences": ["Food & Beverage", "Prepared Foods", "Bulk Dry Goods", "Canned Goods", "Dairy"],
            "budget_min": 1000.0,
            "budget_max": 10000.0,
            "location": "Boston, MA",
            "notes": "Restaurant supply procurement company sourcing bulk surplus food for Boston-area restaurants and food service providers. Looking for large quantities of dry goods, canned goods, dairy, and prepared food ingredients.",
        },
    },

    # ── SMB Gyms & Athletic Businesses ───────────────────────────────────────
    {
        "email": "southendgym@demo.com",
        "name": "South End Strength & Fitness",
        "segment": "smb",
        "profile": {
            "segment": "smb",
            "preferences": ["Men's Athletic Apparel", "Women's Athletic Apparel", "Men's Grooming", "Men's Footwear", "Outdoor & Sporting Goods"],
            "budget_min": 300.0,
            "budget_max": 3000.0,
            "location": "South End, Boston, MA",
            "notes": "Independent gym and fitness studio in South End. Purchases surplus athletic clothing to resell or provide to members — men's workout shirts, shorts, and athletic shoes. Also interested in grooming products for gym changing rooms.",
        },
    },
    {
        "email": "cambridgecrossfit@demo.com",
        "name": "Cambridge CrossFit Box",
        "segment": "smb",
        "profile": {
            "segment": "smb",
            "preferences": ["Men's Athletic Apparel", "Women's Athletic Apparel", "Men's Footwear", "Outdoor & Sporting Goods"],
            "budget_min": 200.0,
            "budget_max": 2000.0,
            "location": "Cambridge, MA",
            "notes": "CrossFit affiliate gym in Cambridge. Buys surplus athletic clothing and shoes for member merchandise program. Looking for Nike, Under Armour, Adidas, and Lululemon surplus men's and women's athletic gear.",
        },
    },
    {
        "email": "maldenathleticclub@demo.com",
        "name": "Malden Athletic Club",
        "segment": "smb",
        "profile": {
            "segment": "smb",
            "preferences": ["Men's Athletic Apparel", "Women's Athletic Apparel", "Food & Beverage", "Beverages", "Men's Grooming"],
            "budget_min": 200.0,
            "budget_max": 2500.0,
            "location": "Malden, MA",
            "notes": "Community gym and fitness center in Malden. Needs men's and women's athletic clothing for member sales and programs. Also interested in beverages and food for gym café and grooming products for locker rooms.",
        },
    },

    # ── SMB Restaurants & Cafés ───────────────────────────────────────────────
    {
        "email": "newburycafe@demo.com",
        "name": "Newbury Street Café & Bistro",
        "segment": "smb",
        "profile": {
            "segment": "smb",
            "preferences": ["Food & Beverage", "Beverages", "Baked Goods", "Dairy", "Prepared Foods"],
            "budget_min": 500.0,
            "budget_max": 5000.0,
            "location": "Boston, MA",
            "notes": "Independent café and bistro on Newbury Street. Sources surplus food inventory including coffee, baked goods, dairy, and specialty food items at below-wholesale prices.",
        },
    },
    {
        "email": "jamaicaplaingrocer@demo.com",
        "name": "Jamaica Plain Grocery & Deli",
        "segment": "smb",
        "profile": {
            "segment": "smb",
            "preferences": ["Food & Beverage", "Produce", "Dairy", "Packaged Groceries", "Canned Goods", "Beverages"],
            "budget_min": 300.0,
            "budget_max": 4000.0,
            "location": "Jamaica Plain, MA",
            "notes": "Small independent grocery store and deli in Jamaica Plain. Sources surplus food inventory including produce, dairy, packaged goods, and beverages for neighborhood grocery retail.",
        },
    },
    {
        "email": "cambridgecoffeeroasters@demo.com",
        "name": "Cambridge Coffee Roasters",
        "segment": "smb",
        "profile": {
            "segment": "smb",
            "preferences": ["Beverages", "Food & Beverage", "Baked Goods"],
            "budget_min": 500.0,
            "budget_max": 4000.0,
            "location": "Cambridge, MA",
            "notes": "Independent coffee roaster and café in Cambridge. Sources surplus coffee, teas, and baked goods from larger coffee brands and bakeries for retail and wholesale supply.",
        },
    },
    {
        "email": "somervilleartisanbakery@demo.com",
        "name": "Somerville Artisan Bakery",
        "segment": "smb",
        "profile": {
            "segment": "smb",
            "preferences": ["Baked Goods", "Food & Beverage", "Dairy", "Bulk Dry Goods"],
            "budget_min": 300.0,
            "budget_max": 3000.0,
            "location": "Somerville, MA",
            "notes": "Small artisan bakery in Somerville sourcing surplus flour, butter, eggs, and bakery ingredients at below-wholesale prices to supplement production.",
        },
    },
    {
        "email": "bostoncorporatecatering@demo.com",
        "name": "Boston Corporate Catering",
        "segment": "smb",
        "profile": {
            "segment": "smb",
            "preferences": ["Prepared Foods", "Food & Beverage", "Beverages", "Baked Goods", "Dairy"],
            "budget_min": 1000.0,
            "budget_max": 8000.0,
            "location": "Boston, MA",
            "notes": "Corporate catering company serving Boston's financial district. Sources surplus prepared foods, beverages, and baked goods to supplement catering offerings at below-retail prices.",
        },
    },

    # ── SMB Fashion & Beauty Boutiques ────────────────────────────────────────
    {
        "email": "mensboutiquebeacon@demo.com",
        "name": "Beacon Hill Men's Boutique",
        "segment": "smb",
        "profile": {
            "segment": "smb",
            "preferences": ["Men's Clothing", "Men's Outerwear", "Men's Footwear", "Men's Grooming"],
            "budget_min": 500.0,
            "budget_max": 5000.0,
            "location": "Boston, MA",
            "notes": "Upscale men's clothing boutique in Beacon Hill. Sources surplus premium men's clothing from Ralph Lauren, Brooks Brothers, and J.Crew for below-retail resale. Also interested in men's grooming products.",
        },
    },
    {
        "email": "southendbarbershop@demo.com",
        "name": "South End Barbershop",
        "segment": "smb",
        "profile": {
            "segment": "smb",
            "preferences": ["Men's Grooming", "Beauty & Personal Care"],
            "budget_min": 200.0,
            "budget_max": 2000.0,
            "location": "South End, Boston, MA",
            "notes": "Traditional barbershop in South End. Sources surplus men's grooming products including Gillette razors, American Crew styling products, Jack Black skincare, and Old Spice at below-wholesale prices.",
        },
    },
    {
        "email": "beautybouttique@demo.com",
        "name": "Boutique Beauty Studio Boston",
        "segment": "smb",
        "profile": {
            "segment": "smb",
            "preferences": ["Makeup & Cosmetics", "Beauty & Skincare", "Beauty & Hair Care", "Women's Accessories"],
            "budget_min": 400.0,
            "budget_max": 4000.0,
            "location": "Boston, MA",
            "notes": "Beauty studio and makeup boutique in Boston. Sources surplus makeup and skincare products from Fenty Beauty, MAC, Tarte, Urban Decay, and similar brands for retail sales and client use.",
        },
    },
    {
        "email": "backbayathletica@demo.com",
        "name": "Back Bay Athletic Boutique",
        "segment": "smb",
        "profile": {
            "segment": "smb",
            "preferences": ["Women's Athletic Apparel", "Men's Athletic Apparel", "Men's Footwear", "Women's Footwear"],
            "budget_min": 500.0,
            "budget_max": 5000.0,
            "location": "Back Bay, Boston, MA",
            "notes": "Upscale athletic apparel boutique in Back Bay. Sources surplus Lululemon, Athleta, Nike, and Adidas athletic clothing for women and men at below-wholesale prices for boutique resale.",
        },
    },

    # ── More Diverse Buyer Profiles ───────────────────────────────────────────
    {
        "email": "bostonschools@demo.com",
        "name": "Boston Public Schools Food Service",
        "segment": "nonprofit",
        "profile": {
            "segment": "nonprofit",
            "preferences": ["Food & Beverage", "Produce", "Dairy", "Bulk Dry Goods", "Packaged Groceries", "Baked Goods", "Beverages"],
            "budget_min": 0.0,
            "budget_max": 5000.0,
            "location": "Boston, MA",
            "notes": "Boston Public Schools food service program sourcing surplus food for school meal programs. Needs fresh produce, dairy, bulk dry goods, baked goods, and packaged groceries for student meal service.",
        },
    },
    {
        "email": "northeasternfoodpantry@demo.com",
        "name": "Northeastern University Food Pantry",
        "segment": "nonprofit",
        "profile": {
            "segment": "nonprofit",
            "preferences": ["Food & Beverage", "Packaged Groceries", "Canned Goods", "Baked Goods", "Beverages", "Bulk Dry Goods"],
            "budget_min": 0.0,
            "budget_max": 0.0,
            "location": "Boston, MA",
            "notes": "Campus food pantry serving food-insecure Northeastern University students. Needs packaged groceries, canned goods, baked goods, and beverages for free student distribution.",
        },
    },
    {
        "email": "bostoncollegeresources@demo.com",
        "name": "Boston College Student Resources",
        "segment": "nonprofit",
        "profile": {
            "segment": "nonprofit",
            "preferences": ["Food & Beverage", "Packaged Groceries", "Beverages", "Men's Clothing", "Women's Clothing"],
            "budget_min": 0.0,
            "budget_max": 1000.0,
            "location": "Chestnut Hill, MA",
            "notes": "Boston College student support services program. Sources food and clothing for students in financial need — food pantry, professional clothing closet for job interviews, and emergency supplies.",
        },
    },
    {
        "email": "harvardfoodbank@demo.com",
        "name": "Harvard Food Pantry",
        "segment": "nonprofit",
        "profile": {
            "segment": "nonprofit",
            "preferences": ["Food & Beverage", "Packaged Groceries", "Produce", "Canned Goods", "Dairy", "Beverages"],
            "budget_min": 0.0,
            "budget_max": 0.0,
            "location": "Cambridge, MA",
            "notes": "Harvard University food pantry supporting graduate students and university employees facing food insecurity. Needs packaged groceries, produce, canned goods, and beverages.",
        },
    },
    {
        "email": "masshire@demo.com",
        "name": "MassHire Boston Career Center",
        "segment": "nonprofit",
        "profile": {
            "segment": "nonprofit",
            "preferences": ["Men's Clothing", "Women's Clothing", "Men's Footwear", "Women's Footwear", "Men's Grooming"],
            "budget_min": 0.0,
            "budget_max": 500.0,
            "location": "Boston, MA",
            "notes": "State career center helping job seekers in Boston. Maintains professional clothing closet for job interviews — needs men's and women's professional clothing, dress shoes, and grooming products for clients.",
        },
    },
    {
        "email": "urbanleagueboston@demo.com",
        "name": "Urban League of Eastern Massachusetts",
        "segment": "nonprofit",
        "profile": {
            "segment": "nonprofit",
            "preferences": ["Men's Clothing", "Women's Clothing", "Men's Grooming", "Food & Beverage", "Men's Footwear"],
            "budget_min": 0.0,
            "budget_max": 1000.0,
            "location": "Boston, MA",
            "notes": "Empowers African Americans and other underserved communities through economic development programs. Maintains professional clothing program with men's and women's business clothing, grooming products, and job-readiness resources.",
        },
    },
    {
        "email": "missionhill@demo.com",
        "name": "Mission Hill Community Food Pantry",
        "segment": "nonprofit",
        "profile": {
            "segment": "nonprofit",
            "preferences": ["Food & Beverage", "Produce", "Canned Goods", "Packaged Groceries", "Baked Goods", "Dairy"],
            "budget_min": 0.0,
            "budget_max": 0.0,
            "location": "Mission Hill, Boston, MA",
            "notes": "Community food pantry in Mission Hill neighborhood. Distributes food weekly to 200+ families. All food categories accepted — produce, canned goods, packaged groceries, dairy, and baked goods.",
        },
    },
    {
        "email": "eastbostoncommunit@demo.com",
        "name": "East Boston Community Soup Kitchen",
        "segment": "nonprofit",
        "profile": {
            "segment": "nonprofit",
            "preferences": ["Prepared Foods", "Food & Beverage", "Produce", "Canned Goods", "Baked Goods"],
            "budget_min": 0.0,
            "budget_max": 0.0,
            "location": "East Boston, MA",
            "notes": "Volunteer-run soup kitchen serving East Boston's immigrant community. Needs prepared food, fresh produce, and canned goods for daily hot meal service.",
        },
    },
    {
        "email": "outdoorclub@demo.com",
        "name": "Boston Outdoor Recreation Club",
        "segment": "nonprofit",
        "profile": {
            "segment": "nonprofit",
            "preferences": ["Men's Outerwear", "Men's Athletic Apparel", "Women's Athletic Apparel", "Outdoor & Sporting Goods", "Men's Footwear"],
            "budget_min": 0.0,
            "budget_max": 1000.0,
            "location": "Boston, MA",
            "notes": "Community outdoor recreation club connecting Boston youth and adults to nature activities. Provides surplus outdoor clothing and gear to low-income members — men's and women's hiking jackets, outdoor footwear, and camping equipment.",
        },
    },
    {
        "email": "immigrantresettlement@demo.com",
        "name": "International Rescue Committee Boston",
        "segment": "nonprofit",
        "profile": {
            "segment": "nonprofit",
            "preferences": ["Men's Clothing", "Women's Clothing", "Men's Outerwear", "Home Goods", "Food & Beverage", "Men's Footwear", "Women's Footwear"],
            "budget_min": 0.0,
            "budget_max": 0.0,
            "location": "Boston, MA",
            "notes": "Resettles refugees and immigrants in Greater Boston. Urgently needs complete household setups — clothing for all genders, home goods, bedding, and food for newly arrived refugee families.",
        },
    },
    {
        "email": "reentryboston@demo.com",
        "name": "Boston Reentry Initiative",
        "segment": "nonprofit",
        "profile": {
            "segment": "nonprofit",
            "preferences": ["Men's Clothing", "Men's Grooming", "Men's Footwear", "Food & Beverage", "Men's Underwear & Basics"],
            "budget_min": 0.0,
            "budget_max": 0.0,
            "location": "Boston, MA",
            "notes": "Supports formerly incarcerated men returning to Boston. Provides men's clothing for job interviews, men's work boots, men's underwear and socks, and grooming products for reentry into the workforce.",
        },
    },
    {
        "email": "bostonlgbtq@demo.com",
        "name": "Boston LGBTQ+ Community Center",
        "segment": "nonprofit",
        "profile": {
            "segment": "nonprofit",
            "preferences": ["Men's Clothing", "Women's Clothing", "Apparel", "Makeup & Cosmetics", "Beauty & Skincare", "Food & Beverage"],
            "budget_min": 0.0,
            "budget_max": 500.0,
            "location": "Boston, MA",
            "notes": "Community resource center for LGBTQ+ individuals and families in Boston. Maintains clothing closet with all genders' clothing, makeup and beauty products, and food pantry for LGBTQ+ youth and adults.",
        },
    },
    {
        "email": "transitionalhousing@demo.com",
        "name": "Heading Home Transitional Housing",
        "segment": "nonprofit",
        "profile": {
            "segment": "nonprofit",
            "preferences": ["Home Goods", "Men's Clothing", "Women's Clothing", "Food & Beverage", "Canned Goods", "Men's Underwear & Basics"],
            "budget_min": 0.0,
            "budget_max": 0.0,
            "location": "Boston, MA",
            "notes": "Transitional housing nonprofit moving individuals from homelessness to permanent housing. Needs home goods to furnish apartments — kitchen items, bedding, towels — plus clothing and food for residents transitioning to independent living.",
        },
    },

    # ── More Multi-Category Buyers ────────────────────────────────────────────
    {
        "email": "fitnessfoodreseller@demo.com",
        "name": "Boston Fitness & Food Reseller",
        "segment": "reseller",
        "profile": {
            "segment": "reseller",
            "preferences": ["Men's Athletic Apparel", "Women's Athletic Apparel", "Food & Beverage", "Beverages", "Men's Grooming"],
            "budget_min": 300.0,
            "budget_max": 4000.0,
            "location": "Boston, MA",
            "notes": "Multi-category reseller targeting gym and fitness market. Buys surplus athletic clothing from Nike, Adidas, Under Armour, and Lululemon, plus surplus food and beverages for fitness market resale.",
        },
    },
    {
        "email": "groomingandfood@demo.com",
        "name": "Urban Men's Care — Grooming & Food",
        "segment": "reseller",
        "profile": {
            "segment": "reseller",
            "preferences": ["Men's Grooming", "Food & Beverage", "Beverages", "Men's Clothing"],
            "budget_min": 200.0,
            "budget_max": 3000.0,
            "location": "Boston, MA",
            "notes": "Multi-category surplus reseller targeting urban men's market. Sources men's grooming products (Gillette, Old Spice, Jack Black, American Crew) and food and beverages for resale through urban retail channels.",
        },
    },
    {
        "email": "beautyandfood@demo.com",
        "name": "Boston Beauty & Specialty Foods",
        "segment": "reseller",
        "profile": {
            "segment": "reseller",
            "preferences": ["Makeup & Cosmetics", "Beauty & Skincare", "Food & Beverage", "Beverages", "Packaged Groceries"],
            "budget_min": 300.0,
            "budget_max": 4000.0,
            "location": "Boston, MA",
            "notes": "Multi-category reseller combining beauty products with specialty food. Sources surplus makeup from Fenty, MAC, and Tarte alongside specialty food and beverages for multi-category retail.",
        },
    },
    {
        "email": "clothingfoodnonprofit@demo.com",
        "name": "All-Needs Community Center Boston",
        "segment": "nonprofit",
        "profile": {
            "segment": "nonprofit",
            "preferences": ["Men's Clothing", "Women's Clothing", "Food & Beverage", "Produce", "Canned Goods", "Men's Grooming", "Makeup & Cosmetics"],
            "budget_min": 0.0,
            "budget_max": 0.0,
            "location": "Roxbury, MA",
            "notes": "Community center in Roxbury serving all community needs — food pantry, clothing closet, and personal care distribution. Accepts men's and women's clothing, all food categories, men's grooming, and women's beauty products.",
        },
    },
    {
        "email": "mensandwomenshelter@demo.com",
        "name": "Greater Boston Interfaith Shelter",
        "segment": "nonprofit",
        "profile": {
            "segment": "nonprofit",
            "preferences": ["Men's Clothing", "Women's Clothing", "Men's Grooming", "Beauty & Skincare", "Food & Beverage", "Baked Goods", "Men's Underwear & Basics"],
            "budget_min": 0.0,
            "budget_max": 0.0,
            "location": "Boston, MA",
            "notes": "Faith-based interfaith shelter serving men and women experiencing homelessness. Needs men's and women's clothing, food for daily meals, grooming products for both genders, and essentials like underwear and socks.",
        },
    },
]


# ── HTTP helpers ──────────────────────────────────────────────────────────────

async def _upload_item(client: httpx.AsyncClient, token: str, item: dict) -> bool:
    resp = await client.post(
        f"{BASE}/inventory/upload",
        json=item,
        headers={"Authorization": f"Bearer {token}"},
    )
    return resp.status_code == 201



# ── Health check ──────────────────────────────────────────────────────────────

async def check_health(client: httpx.AsyncClient) -> bool:
    try:
        r = await client.get(f"{BASE}/health")
        status = "UP" if r.status_code == 200 else f"ERROR {r.status_code}"
    except httpx.ConnectError:
        status = "DOWN — is the backend running?"
        print(f"    Backend  {BASE}/health  →  {status}")
        return False
    print(f"    Backend  {BASE}/health  →  {status}")
    return r.status_code == 200


# ── Seeding steps ─────────────────────────────────────────────────────────────

async def seed_retailers(client: httpx.AsyncClient, sem: asyncio.Semaphore) -> dict[str, str]:
    print("\n── Registering retailers ─────────────────────────────────────────")
    tokens: dict[str, str] = {}
    created = skipped = failed = 0

    async def _do(r: dict) -> None:
        nonlocal created, skipped, failed
        async with sem:
            signup = await client.post(
                f"{BASE}/auth/signup",
                json={"email": r["email"], "password": PASSWORD, "role": "retailer"},
            )
            if signup.status_code == 201:
                tokens[r["email"]] = signup.json()["access_token"]
                _ok(f"{r['name']}  ({r['email']})")
                created += 1
            elif signup.status_code == 409:
                login = await client.post(f"{BASE}/auth/login", json={"email": r["email"], "password": PASSWORD})
                if login.status_code == 200:
                    tokens[r["email"]] = login.json()["access_token"]
                    _skip(f"{r['name']}  ({r['email']})")
                    skipped += 1
                else:
                    _err(f"{r['name']}  — login failed")
                    failed += 1
            else:
                _err(f"{r['name']}  — signup error {signup.status_code}")
                failed += 1

    await asyncio.gather(*[_do(r) for r in RETAILERS])
    print(f"\n    Retailers: {created} created, {skipped} skipped, {failed} failed")
    return tokens


async def seed_inventory(client: httpx.AsyncClient, sem: asyncio.Semaphore, retailer_tokens: dict[str, str]) -> int:
    print("\n── Uploading inventory ───────────────────────────────────────────")
    total = 0

    for email, items in INVENTORY.items():
        token = retailer_tokens.get(email)
        if not token:
            _warn(f"No token for {email} — skipping inventory")
            continue

        ok_count = 0
        for item in items:
            async with sem:
                success = await _upload_item(client, token, item)
            if success:
                ok_count += 1
            else:
                _warn(f"Failed to upload '{item['title']}' for {email}")

        retailer_name = next((r["name"] for r in RETAILERS if r["email"] == email), email)
        _ok(f"{retailer_name}: {ok_count}/{len(items)} items uploaded")
        total += ok_count

    print(f"\n    Inventory: {total} items total")
    return total


async def seed_buyers(client: httpx.AsyncClient, sem: asyncio.Semaphore) -> dict[str, str]:
    print("\n── Registering buyers ────────────────────────────────────────────")
    tokens: dict[str, str] = {}
    created = skipped = failed = 0

    async def _do(b: dict) -> None:
        nonlocal created, skipped, failed
        async with sem:
            signup = await client.post(
                f"{BASE}/auth/signup",
                json={"email": b["email"], "password": PASSWORD, "role": "buyer"},
            )
            if signup.status_code == 201:
                tokens[b["email"]] = signup.json()["access_token"]
                _ok(f"{b['name']}  ({b['email']})  [{b['segment']}]")
                created += 1
            elif signup.status_code == 409:
                login = await client.post(f"{BASE}/auth/login", json={"email": b["email"], "password": PASSWORD})
                if login.status_code == 200:
                    tokens[b["email"]] = login.json()["access_token"]
                    _skip(f"{b['name']}  ({b['email']})")
                    skipped += 1
                else:
                    _err(f"{b['name']}  — login failed")
                    failed += 1
            else:
                _err(f"{b['name']}  — signup error {signup.status_code}")
                failed += 1

    await asyncio.gather(*[_do(b) for b in BUYERS])
    print(f"\n    Buyers: {created} created, {skipped} skipped, {failed} failed")
    return tokens


async def seed_profiles(client: httpx.AsyncClient, sem: asyncio.Semaphore, buyer_tokens: dict[str, str]) -> int:
    print("\n── Creating buyer profiles ───────────────────────────────────────")
    created = skipped = failed = 0

    async def _do(b: dict) -> None:
        nonlocal created, skipped, failed
        token = buyer_tokens.get(b["email"])
        if not token:
            _warn(f"No token for {b['email']} — skipping profile")
            return
        async with sem:
            resp = await client.post(
                f"{BASE}/buyer/onboarding",
                json=b["profile"],
                headers={"Authorization": f"Bearer {token}"},
            )
        if resp.status_code == 201:
            _ok(f"{b['name']}  [{b['segment']}]")
            created += 1
        elif resp.status_code == 409:
            _skip(f"{b['name']}")
            skipped += 1
        else:
            _err(f"{b['name']}  — profile error: {resp.status_code} {resp.text}")
            failed += 1

    await asyncio.gather(*[_do(b) for b in BUYERS])
    print(f"\n    Profiles: {created} created, {skipped} skipped, {failed} failed")
    return created


# ── Main ──────────────────────────────────────────────────────────────────────

async def main() -> None:
    print("═" * 62)
    print("  VGP PLATFORM — Boston Demo Data Seeder (Expanded)")
    print("═" * 62)

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:

        print("\n── Service health ────────────────────────────────────────────")
        healthy = await check_health(client)
        if not healthy:
            print("\nERROR: Backend is not reachable. Start it first:\n  uvicorn app:app --port 8000 --reload\n", file=sys.stderr)
            sys.exit(1)

        sem = asyncio.Semaphore(CONCURRENCY)

        retailer_tokens = await seed_retailers(client, sem)
        item_count      = await seed_inventory(client, sem, retailer_tokens)
        buyer_tokens    = await seed_buyers(client, sem)
        profile_count   = await seed_profiles(client, sem, buyer_tokens)

    print("\n" + "═" * 62)
    print("  SEED COMPLETE")
    print("═" * 62)
    print(f"  Retailers  : {len(retailer_tokens)} accounts")
    print(f"  Inventory  : {item_count} items")
    print(f"  Buyers     : {len(buyer_tokens)} accounts")
    print(f"  Profiles   : {profile_count} buyer profiles")
    print()
    print("  Password for all accounts : Test1234!")
    print(f"  API docs    : {BASE}/docs")
    print("═" * 62)
    print()
    print("  Demo searches to try:")
    print("  Business side: 'food', 'baked goods', 'makeup', 'cosmetics',")
    print("                 'women clothing', 'accessories', 'beverages'")
    print("  Buyer side:    'food', 'pastries', 'makeup', 'cosmetics',")
    print("                 'women accessories', 'clothing', 'skincare'")
    print("═" * 62)


if __name__ == "__main__":
    asyncio.run(main())
