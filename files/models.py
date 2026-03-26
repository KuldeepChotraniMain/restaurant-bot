"""
models.py — schema DDL + full aosa menu seed data
"""

import json
import random
import uuid
from datetime import datetime, timedelta

from database import raw_connection


# ── helpers ──────────────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ── DDL ──────────────────────────────────────────────────────────────────────

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS venues (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    type        TEXT NOT NULL,
    description TEXT,
    address     TEXT,
    created_at  TEXT
);

CREATE TABLE IF NOT EXISTS categories (
    id         TEXT PRIMARY KEY,
    venue_id   TEXT NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    name       TEXT NOT NULL,
    sort_order INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS menu_items (
    id           TEXT PRIMARY KEY,
    venue_id     TEXT NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    category_id  TEXT REFERENCES categories(id) ON DELETE SET NULL,
    name         TEXT NOT NULL,
    description  TEXT,
    price        REAL NOT NULL,
    is_veg       INTEGER DEFAULT 0,
    is_vegan     INTEGER DEFAULT 0,
    is_available INTEGER DEFAULT 1,
    tags         TEXT DEFAULT '[]',
    created_at   TEXT
);

CREATE TABLE IF NOT EXISTS orders (
    id                   TEXT PRIMARY KEY,
    venue_id             TEXT NOT NULL,
    customer_name        TEXT,
    table_ref            TEXT,
    order_type           TEXT NOT NULL,
    spice_level          TEXT,
    dietary_pref         TEXT DEFAULT '[]',
    portion_size         TEXT,
    special_instructions TEXT,
    total_amount         REAL DEFAULT 0,
    status               TEXT DEFAULT 'pending',
    created_at           TEXT,
    hour_of_day          INTEGER,
    day_of_week          TEXT
);

CREATE TABLE IF NOT EXISTS order_items (
    id           TEXT PRIMARY KEY,
    order_id     TEXT NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    menu_item_id TEXT NOT NULL,
    name         TEXT NOT NULL,
    price        REAL NOT NULL,
    quantity     INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id         TEXT PRIMARY KEY,
    venue_id   TEXT NOT NULL,
    session_id TEXT NOT NULL,
    role       TEXT NOT NULL,
    content    TEXT NOT NULL,
    created_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_orders_venue   ON orders(venue_id);
CREATE INDEX IF NOT EXISTS idx_orders_hour    ON orders(hour_of_day);
CREATE INDEX IF NOT EXISTS idx_items_venue    ON menu_items(venue_id);
CREATE INDEX IF NOT EXISTS idx_chat_session   ON chat_messages(session_id);
"""


# ── full menu definition ──────────────────────────────────────────────────────
# Each entry: (name, description, price, is_veg, is_vegan, [tags])

MENU: dict[str, list[tuple]] = {
    "All Day Breakfast": [
        ("French Omelette",                 "Served with baby potatoes & pan seared cherry tomatoes",    300, 1, 0, ["eggs", "breakfast", "light"]),
        ("Masala Omelette",                 "Onion | Tomato | Chilli | Coriander",                       300, 1, 0, ["eggs", "breakfast", "spicy", "indian"]),
        ("Cheese Omelette",                 "English Cheddar",                                            300, 1, 0, ["eggs", "breakfast", "cheesy"]),
        ("Skinny Omelette",                 "Egg Whites — light and healthy",                             300, 1, 0, ["eggs", "breakfast", "healthy", "light"]),
        ("Eggs Ben-Addict",                 "Poached Eggs | Chicken Ham | English Muffin | Hollandaise", 350, 0, 0, ["eggs", "breakfast", "hearty"]),
        ("Eggs Florentine",                 "Poached Eggs | Sautéed Spinach | English Muffin | Hollandaise", 350, 1, 0, ["eggs", "breakfast", "vegetarian", "light"]),
        ("Mushroom & Bell Pepper Frittata", "Light pastry topped with creamy mushroom and parmesan",     350, 1, 0, ["eggs", "breakfast", "vegetarian", "mushroom"]),
        ("Mustard Upma",                    "Quinoa | Tomato & Coconut Chutney | Cashew | Curry Leaf",   350, 1, 1, ["breakfast", "indian", "vegan", "healthy"]),
    ],
    "Toasts & Pancakes": [
        ("Shakshuka with Toast",            "Wilted Spinach | Spicy Sauce",                               350, 1, 0, ["eggs", "spicy", "vegetarian", "toast"]),
        ("Nutella French Toast",            "Whipped Cream | Hazelnuts",                                  400, 1, 0, ["sweet", "toast", "indulgent", "nutella"]),
        ("Pancake Stack",                   "Mix Fruit Jam | Whipped Cream | Banana Caramel Sauce",       400, 1, 0, ["sweet", "pancakes", "breakfast", "indulgent"]),
        ("Buckwheat & Chickpea Pancakes",   "Hummus | Homemade Chutneys | House Rucola Salad",            350, 1, 1, ["healthy", "vegan", "pancakes", "light"]),
    ],
    "Sandwiches": [
        ("Italian Sandwich",                "Fresh Mozzarella | Rocket Leaf | Focaccia",                  450, 1, 0, ["sandwich", "vegetarian", "italian", "light"]),
        ("Med Pita Sandwich",               "Avocado | Cucumber | Hummus",                                400, 1, 1, ["sandwich", "vegan", "healthy", "light"]),
        ("Chipotle Chicken Sandwich",       "Fried Egg | Focaccia",                                       500, 0, 0, ["sandwich", "chicken", "spicy", "hearty"]),
        ("Lamb Sandwich",                   "Rocket | Feta | Lamb Pepperoni | Pepper Relish | Ciabatta",  525, 0, 0, ["sandwich", "lamb", "hearty", "premium"]),
    ],
    "Sides": [
        ("Sides Platter", "Toast | Baked Beans | Hash Browns | Chicken Sausages | Potato Wedges", 100, 0, 0, ["sides", "light", "breakfast"]),
    ],
    "Smoothie Jars": [
        ("Green Apple & Avocado Smoothie Jar", "Granola | Chia | Banana | Coconut Flakes",    350, 1, 1, ["healthy", "smoothie", "vegan", "fresh"]),
        ("Berry Smoothie Jar",                 "Granola | Berries | Yoghurt",                 350, 1, 0, ["healthy", "smoothie", "fresh", "sweet"]),
        ("Chocolate & Coconut Smoothie Jar",   "Dates | Walnuts | Brownie Bites",             350, 1, 1, ["sweet", "smoothie", "vegan", "indulgent"]),
    ],
    "Salads": [
        ("Rocket & Red Wine Poached Pear Salad", "Mango Chunda | Feta",            520, 1, 0, ["salad", "light", "vegetarian", "healthy"]),
        ("Quinoa Chicken Salad",                  "Chilli | Sweet Peas",            525, 0, 0, ["salad", "healthy", "protein", "light"]),
        ("Barley Moong Sprout Salad",             "Corn | Savoury Schnapps",        400, 1, 1, ["salad", "healthy", "vegan", "light"]),
    ],
    "Flatbreads": [
        ("Italian Lifestyle Flatbread",  "Basil | Mozzarella",                           500, 1, 0, ["flatbread", "vegetarian", "italian", "cheesy"]),
        ("Spinachi Truffle Flatbread",   "Truffle Oil | Spinach | Garlic",               580, 1, 0, ["flatbread", "vegetarian", "premium", "truffle"]),
        ("Pesto Balsamic Flatbread",     "Pesto | Pinenut | Rocket Leaves",              650, 1, 0, ["flatbread", "vegetarian", "premium"]),
        ("Pepper Shroom Flatbread",      "Bell Pepper | Mushroom",                       550, 1, 1, ["flatbread", "vegan", "vegetarian"]),
        ("Pesto Paneer Flatbread",       "Onion | Pinenut | Rucola",                     580, 1, 0, ["flatbread", "vegetarian", "paneer"]),
        ("Smoked Chicken Flatbread",     "Basil Oil",                                    625, 0, 0, ["flatbread", "chicken", "smoky"]),
        ("Lamb Pepperoni Flatbread",     "Pickled Chilli | Parmesan Shavings",           650, 0, 0, ["flatbread", "lamb", "spicy", "premium"]),
    ],
    "A Little Mix": [
        ("Soya Keema",              "Freshly Baked Pav",                              375, 1, 1, ["indian", "vegan", "spicy", "hearty"]),
        ("Masala Fish Fingers",     "Garlic Chutney | Jeera Tartar Sauce",            450, 0, 0, ["fish", "indian", "spicy", "crispy"]),
        ("Aloo Bravas",             "Pepper Refresh Relish | Potato Foam",            400, 1, 1, ["potato", "vegan", "spicy", "crispy"]),
        ("Massaman Curry",          "Jasmine Rice",                                   575, 1, 1, ["curry", "vegan", "thai", "hearty"]),
        ("Tamarind Curry",          "Husked Barley",                                  550, 1, 1, ["curry", "vegan", "indian", "tangy"]),
        ("Chifferi Cacio e Pepe",   "Parmesan | Black Pepper | Cream",               475, 1, 0, ["pasta", "vegetarian", "cheesy", "creamy"]),
        ("Fettuccini Arrabiata",    "Tomato | Chilli | Basil",                        450, 1, 1, ["pasta", "vegan", "spicy", "italian"]),
        ("Penne Pesto",             "Pesto | Chicken | Parmesan",                     550, 0, 0, ["pasta", "chicken", "creamy"]),
        ("Linguini Aglio e Olio",   "Orange | Prawns | Butter & Parmesan Emulsion",  650, 0, 0, ["pasta", "seafood", "premium", "butter"]),
        ("Healing Vegetable Kedgeree", "Roasted Papadums",                            350, 1, 1, ["indian", "vegan", "healthy", "rice"]),
    ],
    "Aosa Specials": [
        ("Mezze Platter",                          "A selection of house mezze",                               599, 1, 0, ["sharing", "vegetarian", "light"]),
        ("Burrito Bowl",                           "Hearty burrito bowl with assorted condiments",             499, 1, 0, ["mexican", "vegetarian", "hearty"]),
        ("Nacho Bowl",                             "Classic nacho bowl",                                       499, 1, 0, ["mexican", "vegetarian", "cheesy", "crispy"]),
        ("Mushroom Tartine on Toast",              "Add Poached Egg ₹150 | Add Chicken Ham ₹150",              380, 1, 0, ["toast", "vegetarian", "mushroom", "light"]),
        ("Homemade Soft Shell Fried Chicken Tacos","Crispy fried chicken tacos",                               475, 0, 0, ["tacos", "chicken", "crispy", "hearty"]),
        ("Homemade Soft Shell Fried Paneer Tacos", "Crispy fried paneer tacos",                                450, 1, 0, ["tacos", "vegetarian", "paneer", "crispy"]),
        ("Ham Mustard & Cheese Croissant",         "Buttery croissant with ham and cheese",                   400, 0, 0, ["croissant", "ham", "cheesy"]),
        ("Caprese Croissant",                      "Fresh caprese in a flaky croissant",                       350, 1, 0, ["croissant", "vegetarian", "fresh"]),
        ("Cheese Omelette Croissant",              "Omelette tucked inside a warm croissant",                 350, 1, 0, ["croissant", "vegetarian", "eggs"]),
        ("Pistachio Crusted Grilled Chicken",      "With English Vegetables Mash",                            499, 0, 0, ["chicken", "premium", "hearty"]),
    ],
    "Hot Coffee": [
        ("Espresso",                      "A concentrated shot of coffee",                                    140, 1, 1, ["coffee", "hot", "strong"]),
        ("Ristretto",                     "More concentrated and shorter than espresso",                      140, 1, 1, ["coffee", "hot", "strong"]),
        ("Macchiato",                     "Espresso with a dash of milk froth",                               140, 1, 1, ["coffee", "hot"]),
        ("Americano",                     "Espresso topped with hot water",                                   180, 1, 1, ["coffee", "hot", "light"]),
        ("Long Black",                    "Double espresso with hot water — stronger",                        200, 1, 1, ["coffee", "hot", "strong"]),
        ("Cappuccino",                    "Coffee, warm milk and lots of milk foam",                          240, 1, 0, ["coffee", "hot", "creamy", "signature"]),
        ("Cafe Latte",                    "Hot coffee with steamed milk and less foam",                       240, 1, 0, ["coffee", "hot", "creamy", "mild"]),
        ("Flat White",                    "Steamed milk, almost no foam — hottest milk option",               240, 1, 0, ["coffee", "hot", "creamy"]),
        ("Cortado",                       "Shorter than a latte, more milk, more strength",                   240, 1, 0, ["coffee", "hot", "strong"]),
        ("Cafe Latte Flavoured",          "Latte with your choice of flavour",                                250, 1, 0, ["coffee", "hot", "sweet", "flavoured"]),
        ("Mocha",                         "Coffee & chocolate together — a perfect match",                    260, 1, 0, ["coffee", "hot", "chocolate", "sweet"]),
        ("Salted Caramel Popcorn Latte",  "Cinema salted caramel popcorn but in a coffee cup",               280, 1, 0, ["coffee", "hot", "sweet", "salted caramel", "signature"]),
        ("Spiced C&C Coffee & Cacao",     "Coffee, chocolate and cinnamon spice",                            240, 1, 0, ["coffee", "hot", "spiced", "chocolate"]),
    ],
    "Cold Brew": [
        ("Cold Brew Classic",         "Classic cold brew served with ice",                                   190, 1, 1, ["coffee", "cold", "signature"]),
        ("Flavoured Cold Brew",       "Cold brew with your choice of flavour",                               210, 1, 1, ["coffee", "cold", "flavoured"]),
        ("Cold Brew Latte",           "Cold brew and milk together",                                         210, 1, 0, ["coffee", "cold", "creamy"]),
        ("Cold Brew Latte Flavoured", "Milky cold brew with your flavour choice",                            220, 1, 0, ["coffee", "cold", "creamy", "flavoured"]),
        ("Cold Brew Aperol",          "Aperol spritz inspired cold brew drink",                              220, 1, 1, ["coffee", "cold", "unique"]),
        ("Coffee Mojito",             "Fresh mojito with cold brew",                                         240, 1, 1, ["coffee", "cold", "fresh", "mocktail"]),
        ("Coffee Tonic",              "Coffee and tonic with lemon slice — best in town",                    250, 1, 1, ["coffee", "cold", "tonic", "unique"]),
        ("Aosa Coffee Tonic",         "aosa's special version of coffee tonic",                              260, 1, 1, ["coffee", "cold", "signature", "unique"]),
    ],
    "Iced Coffee": [
        ("Iced Latte",                         "Simple cold and iced milk coffee — peoples choice",          240, 1, 0, ["coffee", "cold", "creamy", "popular"]),
        ("Iced Flavoured Latte",               "Iced latte with your choice of flavour",                     260, 1, 0, ["coffee", "cold", "sweet", "flavoured"]),
        ("Iced Magic Latte",                   "Cold coffee with sweetened milk — magic in a cup",           260, 1, 0, ["coffee", "cold", "sweet"]),
        ("Iced Mocha",                         "Coffee and chocolate in an iced version — heavenly",         260, 1, 0, ["coffee", "cold", "chocolate", "sweet"]),
        ("A Very Berry Cafe Latte",            "Iced coffee with milk and strawberry",                       280, 1, 0, ["coffee", "cold", "berry", "fruity"]),
        ("Cafe Frappe",                        "Classic blended cold coffee",                                 250, 1, 0, ["coffee", "cold", "blended"]),
        ("Salted Caramel Popcorn Frappe",      "Cinema salted caramel popcorn as a frappe",                  280, 1, 0, ["coffee", "cold", "sweet", "salted caramel"]),
        ("Caramelised Banana & Vanilla Frappe","Banoffee and coffee and vanilla in cold form",               280, 1, 0, ["coffee", "cold", "sweet", "banana"]),
        ("Flavoured Frappe",                   "Classic coffee frappe with your flavour choice",              260, 1, 0, ["coffee", "cold", "flavoured"]),
        ("Cheesecake Frappe",                  "A cold coffee or a cheesecake? Both.",                       280, 1, 0, ["coffee", "cold", "sweet", "cheesecake"]),
        ("Espresso on the Rocks",              "Like whisky on rocks — but espresso",                        150, 1, 1, ["coffee", "cold", "strong"]),
        ("Iced Americano",                     "Cold black coffee, espresso, ice & water",                   180, 1, 1, ["coffee", "cold", "strong", "light"]),
        ("Iced Long Black",                    "Double espresso, cold, ice and water",                       200, 1, 1, ["coffee", "cold", "strong"]),
    ],
    "Aosa Coffee Specials": [
        ("Vietnamese Styled Hot Coffee",  "Vietnamese style with condensed milk, hot version",              280, 1, 0, ["coffee", "hot", "vietnamese", "sweet", "signature"]),
        ("Vietnamese Styled Iced Coffee", "Vietnamese style with condensed milk, iced shaken — top selling",280, 1, 0, ["coffee", "cold", "vietnamese", "sweet", "signature"]),
        ("Espresso Martini",              "Virgin espresso martini — must try",                              260, 1, 0, ["coffee", "cold", "mocktail", "premium"]),
        ("Espresso Bull",                 "Caffeine max — espresso and red bull",                            300, 1, 1, ["coffee", "cold", "energy", "strong"]),
        ("South Indian Filter Coffee",   "Classic South Indian filter coffee",                               240, 1, 0, ["coffee", "hot", "south indian", "traditional"]),
        ("Hot Chocolate",                 "Rich warming hot chocolate",                                      240, 1, 0, ["chocolate", "hot", "sweet", "comfort"]),
    ],
    "Affogato": [
        ("Coffee Mochagato",  "Chocolate icecream, espresso and pink salt",            150, 1, 0, ["coffee", "dessert", "chocolate", "sweet"]),
        ("Coffee Affogato",   "Classic vanilla ice cream and espresso shot",           180, 1, 0, ["coffee", "dessert", "vanilla", "sweet"]),
        ("Coffee Conegato",   "aosa's twist on affogato — must try",                  200, 1, 0, ["coffee", "dessert", "signature", "sweet"]),
    ],
    "Tea": [
        ("Masala Chai Pot",                  "Classic Indian spiced chai",              180, 1, 0, ["tea", "hot", "spiced", "indian"]),
        ("Single Malt Grand Bru Assam Leaves","Premium Assam tea",                     210, 1, 0, ["tea", "hot", "premium", "assam"]),
        ("White Tea Saffron Leaves",         "Delicate white tea with saffron",         210, 1, 1, ["tea", "hot", "premium", "light"]),
        ("Jasmine Hot Tea",                  "Floral jasmine tea",                      210, 1, 1, ["tea", "hot", "floral", "light"]),
        ("Macha Latte",                      "Warm matcha latte",                       240, 1, 0, ["tea", "hot", "matcha", "creamy"]),
        ("Chamomile Tea",                    "Calming chamomile herbal tea",            200, 1, 1, ["tea", "hot", "herbal", "calm", "light"]),
        ("Iced Macha Latte",                 "Cold matcha latte",                       240, 1, 0, ["tea", "cold", "matcha", "creamy"]),
        ("Iced Espresso Macha Latte",        "Coffee meets matcha in an iced version",  260, 1, 0, ["tea", "coffee", "cold", "unique"]),
        ("Classic Lemon Iced Tea",           "Refreshing lemon iced tea",               220, 1, 1, ["tea", "cold", "lemon", "fresh"]),
        ("Lemon Mint Iced Tea",              "Lemon and mint iced tea — must try",      220, 1, 1, ["tea", "cold", "lemon", "mint", "fresh"]),
        ("Strawberry Iced Tea",              "Fruity strawberry iced tea",              220, 1, 1, ["tea", "cold", "strawberry", "fruity"]),
        ("Passion Fruit Iced Tea",           "Tropical passion fruit iced tea",         220, 1, 1, ["tea", "cold", "tropical", "fruity"]),
    ],
    "Manual Pour Over": [
        ("V60 Hot / Iced",            "V60 pour over — specialty coffee",   240, 1, 1, ["coffee", "specialty", "filter", "pour over"]),
        ("Kalita Hot / Iced",         "Kalita wave pour over",               240, 1, 1, ["coffee", "specialty", "filter", "pour over"]),
        ("Origami Hot / Iced",        "Origami dripper pour over",           240, 1, 1, ["coffee", "specialty", "filter", "pour over"]),
        ("Clever Dripper Drip",       "Immersion style pour over",           240, 1, 1, ["coffee", "specialty", "filter"]),
        ("Clever Dripper Immersion",  "Full immersion brew",                 240, 1, 1, ["coffee", "specialty", "filter"]),
    ],
    "Non Coffee Mocktails": [
        ("Mojito",          "Classic fresh mojito",                         220, 1, 1, ["mocktail", "cold", "fresh", "mint"]),
        ("Flavoured Mojito","Mojito with flavour options",                  230, 1, 1, ["mocktail", "cold", "fresh", "flavoured"]),
        ("Pina Colada",     "Pineapple, coconut and cream — no alcohol",    220, 1, 1, ["mocktail", "cold", "tropical", "sweet"]),
    ],
    "Shakes": [
        ("Chocolate Shake",           "Rich chocolate milkshake",              240, 1, 0, ["shake", "cold", "chocolate", "sweet"]),
        ("Strawberry Shake",          "Fresh strawberry milkshake",             240, 1, 0, ["shake", "cold", "strawberry", "sweet"]),
        ("Strawberry Cheesecake Shake","Strawberry cheesecake milkshake",       300, 1, 0, ["shake", "cold", "cheesecake", "sweet", "premium"]),
    ],
    "Soft Drinks": [
        ("Water Bottle",      "Still mineral water",           100, 1, 1, ["water", "cold"]),
        ("Ginger Ale",        "Refreshing ginger ale",         120, 1, 1, ["soft drink", "cold", "ginger"]),
        ("Tonic Water",       "Premium tonic water",           120, 1, 1, ["soft drink", "cold"]),
        ("Red Bull",          "Energy drink",                  250, 1, 1, ["energy", "cold"]),
        ("Cold Press Juices", "Fresh cold pressed juices",     250, 1, 1, ["juice", "cold", "healthy", "fresh"]),
    ],
    "Laminated Pastry": [
        ("Aosa Croissant",              "Classic butter croissant — soft, flaky and golden-brown — signature",       200, 1, 0, ["croissant", "pastry", "buttery", "signature", "bakery"]),
        ("Chocolate Croissant",         "Buttery croissant filled with dark couverture chocolate crème — best selling",280,1, 0, ["croissant", "pastry", "chocolate", "sweet", "bakery"]),
        ("Almond Croissant",            "Sweet almond filling topped with toasted almonds",                          280, 1, 0, ["croissant", "pastry", "almond", "sweet", "bakery"]),
        ("Chocolate Pistachio Cube",    "Flaky cube croissant with chocolate and pistachios — trending",             350, 1, 0, ["croissant", "pastry", "chocolate", "pistachio", "premium", "bakery"]),
        ("Lemon Vanilla Cube",          "Flaky cube croissant with zesty lemon and vanilla custard — trending",      350, 1, 0, ["croissant", "pastry", "lemon", "vanilla", "sweet", "bakery"]),
        ("Mushroom Cream Cheese",       "Flaky pastry topped with creamy mushroom and parmesan",                     200, 1, 0, ["pastry", "mushroom", "savory", "cheesy", "bakery"]),
        ("Veggies Jalapeno & Cheese",   "Flaky pastry with gourmet stuffing and cream cheese",                       200, 1, 0, ["pastry", "vegetarian", "spicy", "cheesy", "bakery"]),
        ("Korean Bun",                  "Classic bun with cream cheese and garlic butter",                           210, 1, 0, ["bun", "korean", "cheesy", "sweet", "bakery"]),
        ("Korean Bun 2.0",              "Spinach, mushroom & corn filling — AOSA favourite",                         230, 1, 0, ["bun", "korean", "vegetarian", "premium", "bakery"]),
        ("Margherita Pizza Danish",     "Golden flaky Danish with tomato, mozzarella & basil",                       220, 1, 0, ["danish", "vegetarian", "pizza", "cheesy", "bakery"]),
        ("Spiced Thai Chicken Puff",    "Thai-spiced chicken in flaky pastry",                                        240, 0, 0, ["puff", "chicken", "spicy", "thai", "bakery"]),
        ("Bhuna Gosht Puff",            "Tender spiced lamb in buttery pastry",                                       240, 0, 0, ["puff", "lamb", "spicy", "hearty", "bakery"]),
    ],
    "Tarts": [
        ("Chocolate Mascarpone Tart", "Buttery pastry with milk couverture coffee ganache",           250, 1, 0, ["tart", "chocolate", "sweet", "premium", "bakery"]),
        ("Queen of Tarts",            "Fresh blueberry and mixed berry compote in buttery shortcrust", 300, 1, 0, ["tart", "berry", "sweet", "premium", "bakery"]),
    ],
    "Cookies": [
        ("Chocolate Hazelnut Cookie", "Rich chocolate cookie with crunchy hazelnuts",       150, 1, 0, ["cookie", "chocolate", "hazelnut", "sweet", "bakery"]),
        ("PB & J Cookie",             "Peanut butter and fruity jam in a crunchy cookie",   140, 1, 0, ["cookie", "peanut butter", "sweet", "bakery"]),
        ("Aosa OMG Cookie",           "Pistachio paste and berry confit cookie",             150, 1, 0, ["cookie", "pistachio", "sweet", "signature", "bakery"]),
    ],
    "Entremets & Bistro Style": [
        ("Dessert Island Brownie",    "Brownie with crunchy chocolate coating",                                  300, 1, 0, ["brownie", "chocolate", "sweet", "indulgent", "bakery"]),
        ("Biscoff Cheesecake",        "Dense and creamy cheesecake with Biscoff flavour",                        320, 1, 0, ["cheesecake", "biscoff", "sweet", "premium", "bakery"]),
        ("New York Cheesecake",       "American-style authentic creamy cheesecake — best in town",               300, 1, 0, ["cheesecake", "sweet", "premium", "classic", "bakery"]),
        ("Messy Mud Tub",             "Chocolate paradise layered to perfection in a box",                       300, 1, 0, ["chocolate", "sweet", "indulgent", "premium", "bakery"]),
        ("Chef Special Petit Antoine","Hazelnut and French biscuit with dark couverture ganache and sponge",     350, 1, 0, ["dessert", "chocolate", "premium", "signature", "bakery"]),
        ("Mille-Feuille",             "Laminated puff pastry with rich chocolate cream",                         300, 1, 0, ["pastry", "chocolate", "sweet", "french", "bakery"]),
        ("Mango & Passion Fruit",     "Tropical blend of mango and passion fruit — trending",                    280, 1, 1, ["dessert", "tropical", "sweet", "fruity", "vegan", "bakery"]),
        ("Vegan Chocolate Cake",      "Indulgent vegan chocolate cake",                                          200, 1, 1, ["cake", "vegan", "chocolate", "sweet", "bakery"]),
        ("Carrot Cake",               "Cinnamon-spiced with cream cheese frosting and walnuts",                  190, 1, 0, ["cake", "carrot", "sweet", "classic", "bakery"]),
        ("Dream Come Blue",           "Blueberry sponge cake — dreamy dessert",                                  320, 1, 0, ["cake", "blueberry", "sweet", "premium", "bakery"]),
        ("Tiramisu Tub",              "Classic tiramisu with mascarpone and Kahlua-soaked ladyfingers",          350, 1, 0, ["tiramisu", "coffee", "sweet", "italian", "premium", "bakery"]),
        ("Osaka Style Roll",          "Japanese-style roll with mixed berry compote — must try",                 190, 1, 0, ["cake", "japanese", "berry", "sweet", "light", "bakery"]),
    ],
    "Tea Cakes": [
        ("Lamington Bar",              "Layers of lamington, chocolate and coconut — must try",         200, 1, 0, ["cake", "chocolate", "sweet", "coconut", "bakery"]),
        ("Chocolate and Orange Cake",  "Moist cake with orange flavour (slice ₹200 / loaf ₹600)",      200, 1, 0, ["cake", "chocolate", "orange", "sweet", "bakery"]),
        ("Lemon Drizzle",              "Lemon teacake with citrus glaze (slice ₹180 / loaf ₹550)",     180, 1, 0, ["cake", "lemon", "sweet", "light", "bakery"]),
        ("Banana Bread with Walnuts",  "Classic banana bread AOSA twist (slice ₹160 / loaf ₹500)",     160, 1, 0, ["bread", "banana", "sweet", "nutty", "bakery"]),
        ("Espresso Crumble Cake",      "Espresso-infused crumble cake (slice ₹200 / loaf ₹600)",       200, 1, 0, ["cake", "coffee", "sweet", "premium", "bakery"]),
    ],
    "Celebration Cakes": [
        ("Lemon Blueberry Cake",          "500g ₹1000 / 1000g ₹1800", 1000, 1, 0, ["cake", "celebration", "lemon", "premium", "bakery"]),
        ("Biscoff Cheesecake Whole",      "500g ₹1200 / 1000g ₹2000", 1200, 1, 0, ["cake", "celebration", "biscoff", "premium", "bakery"]),
        ("Aosa Signature Antoine Cake",   "500g ₹1200 / 1000g ₹2000", 1200, 1, 0, ["cake", "celebration", "signature", "premium", "bakery"]),
        ("Fruit Crumble Cake",            "500g ₹1000 / 1000g ₹1800", 1000, 1, 0, ["cake", "celebration", "fruity", "premium", "bakery"]),
        ("Hazelnut Praline Cake",         "500g ₹1200 / 1000g ₹2000", 1200, 1, 0, ["cake", "celebration", "hazelnut", "premium", "bakery"]),
        ("Espresso Almond Cake",          "500g ₹1000 / 1000g ₹1800", 1000, 1, 0, ["cake", "celebration", "coffee", "premium", "bakery"]),
        ("New York Cheese Cake Whole",    "500g ₹1000 / 1000g ₹1800", 1000, 1, 0, ["cake", "celebration", "cheesecake", "premium", "bakery"]),
        ("100% Chocolate Cake",           "500g ₹1200 / 1000g ₹2000", 1200, 1, 0, ["cake", "celebration", "chocolate", "premium", "bakery"]),
        ("Dream Come Blue Whole",         "500g ₹1200 / 1000g ₹2000", 1200, 1, 0, ["cake", "celebration", "blueberry", "premium", "bakery"]),
    ],
    "Bread": [
        ("Signature Aosa Sourdough",         "Our house sourdough — the one that started it all",          200, 1, 1, ["bread", "sourdough", "signature", "bakery"]),
        ("50% Whole Wheat Sourdough",        "Wholesome and nutty whole wheat sourdough",                  220, 1, 1, ["bread", "sourdough", "healthy", "whole wheat", "bakery"]),
        ("Roasted Garlic & Olive Sourdough", "Garlic and olive oil infused sourdough",                     220, 1, 1, ["bread", "sourdough", "garlic", "savory", "bakery"]),
        ("Pesto & Parmesan Babka",           "Twisted babka with pesto and parmesan",                      250, 1, 0, ["bread", "babka", "pesto", "cheesy", "bakery"]),
        ("Chocolate & Nuts Babka",           "Sweet chocolate babka with mixed nuts",                      250, 1, 0, ["bread", "babka", "chocolate", "sweet", "bakery"]),
        ("Ragi Bread",                       "Healthy ragi grain bread",                                   150, 1, 1, ["bread", "ragi", "healthy", "vegan", "bakery"]),
        ("Sourdough Focaccia",               "Classic Italian herb focaccia",                              200, 1, 1, ["bread", "focaccia", "italian", "vegan", "bakery"]),
        ("Multigrain Country Loaf",          "Hearty multigrain country loaf",                             150, 1, 1, ["bread", "multigrain", "healthy", "vegan", "bakery"]),
    ],
}


# ── seed helpers ─────────────────────────────────────────────────────────────

def _insert_venue(db) -> str:
    vid = str(uuid.uuid4())
    db.execute(
        "INSERT INTO venues (id, name, type, description, address, created_at) VALUES (?,?,?,?,?,?)",
        (
            vid, "aosa", "cafe",
            "Bakehouse & Roastery — A curated selection of culinary treasures, crafted with passion & creativity",
            "Local Café",
            _now(),
        ),
    )
    return vid


def _insert_menu(db, venue_id: str) -> None:
    for sort_idx, (cat_name, items) in enumerate(MENU.items()):
        cat_id = str(uuid.uuid4())
        db.execute(
            "INSERT INTO categories (id, venue_id, name, sort_order) VALUES (?,?,?,?)",
            (cat_id, venue_id, cat_name, sort_idx),
        )
        for name, desc, price, is_veg, is_vegan, tags in items:
            db.execute(
                """INSERT INTO menu_items
                   (id, venue_id, category_id, name, description, price,
                    is_veg, is_vegan, tags, created_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (
                    str(uuid.uuid4()), venue_id, cat_id,
                    name, desc, price, is_veg, is_vegan,
                    json.dumps(tags), _now(),
                ),
            )


def _insert_sample_orders(db, venue_id: str) -> None:
    statuses    = ["completed"] * 4 + ["preparing", "ready"]
    order_types = ["dine-in"] * 2 + ["takeaway"]
    spice_lvls  = ["mild", "medium", "hot", "extra-hot"]
    portions    = ["small", "regular", "regular", "large"]
    days        = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    hour_weights= [1, 2, 4, 6, 8, 5, 3, 8, 9, 10, 7, 5, 8, 9, 6]

    all_items = db.execute(
        "SELECT id, name, price FROM menu_items WHERE venue_id=?", (venue_id,)
    ).fetchall()

    for _ in range(80):
        hour = random.choices(range(8, 23), weights=hour_weights, k=1)[0]
        dt   = datetime.now() - timedelta(days=random.randint(0, 6), hours=random.randint(0, 3))
        dt   = dt.replace(hour=hour)
        oid  = str(uuid.uuid4())

        dietary = json.dumps(
            random.sample(["vegetarian", "vegan", "gluten-free"], k=random.randint(0, 1))
        )

        db.execute(
            """INSERT INTO orders
               (id, venue_id, customer_name, order_type, spice_level, dietary_pref,
                portion_size, total_amount, status, created_at, hour_of_day, day_of_week)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                oid, venue_id, f"Guest {random.randint(1, 99)}",
                random.choice(order_types), random.choice(spice_lvls),
                dietary, random.choice(portions),
                0, random.choice(statuses),
                dt.strftime("%Y-%m-%d %H:%M:%S"), hour, days[dt.weekday()],
            ),
        )

        chosen = random.sample(list(all_items), min(random.randint(1, 3), len(all_items)))
        total  = 0.0
        for item in chosen:
            qty   = random.randint(1, 2)
            price = float(item["price"])
            db.execute(
                "INSERT INTO order_items (id, order_id, menu_item_id, name, price, quantity) VALUES (?,?,?,?,?,?)",
                (str(uuid.uuid4()), oid, item["id"], item["name"], price, qty),
            )
            total += price * qty

        db.execute("UPDATE orders SET total_amount=? WHERE id=?", (round(total, 2), oid))


# ── public entry point ────────────────────────────────────────────────────────

def init_db() -> None:
    """Create schema and seed initial data if the DB is empty."""
    db = raw_connection()
    db.executescript(SCHEMA_SQL)
    db.commit()

    if db.execute("SELECT COUNT(*) FROM venues").fetchone()[0] == 0:
        venue_id = _insert_venue(db)
        _insert_menu(db, venue_id)
        _insert_sample_orders(db, venue_id)
        db.commit()
        print("[seed] aosa Bakehouse & Roastery — database seeded successfully ✓")

    db.close()
