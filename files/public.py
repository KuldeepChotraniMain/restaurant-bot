"""
routes/public.py — customer-facing endpoints
  GET  /api/venues
  GET  /api/venues/<vid>/menu
  POST /api/venues/<vid>/chat
  POST /api/venues/<vid>/orders
"""

import json
import uuid
from datetime import datetime

from flask import Blueprint, jsonify, request

from database import get_db
from services.ai_chat import get_ai_response
from services.nlp import find_dishes

public_bp = Blueprint("public", __name__, url_prefix="/api")


# ── venues ────────────────────────────────────────────────────────────────────

@public_bp.get("/venues")
def list_venues():
    rows = get_db().execute(
        "SELECT id, name, type, description, address FROM venues ORDER BY name"
    ).fetchall()
    return jsonify([dict(r) for r in rows])


# ── menu ─────────────────────────────────────────────────────────────────────

@public_bp.get("/venues/<vid>/menu")
def get_menu(vid: str):
    db   = get_db()
    cats = db.execute(
        "SELECT id, name FROM categories WHERE venue_id=? ORDER BY sort_order", (vid,)
    ).fetchall()

    result = []
    for cat in cats:
        items = db.execute(
            "SELECT id, name, description, price, is_veg, is_vegan, tags "
            "FROM menu_items WHERE category_id=? AND is_available=1",
            (cat["id"],),
        ).fetchall()
        if items:
            result.append(
                {
                    "category": cat["name"],
                    "items": [
                        {
                            **dict(i),
                            "tags":     json.loads(i["tags"]),
                            "is_veg":   bool(i["is_veg"]),
                            "is_vegan": bool(i["is_vegan"]),
                        }
                        for i in items
                    ],
                }
            )
    return jsonify(result)


# ── chat ──────────────────────────────────────────────────────────────────────

@public_bp.post("/venues/<vid>/chat")
def chat(vid: str):
    data          = request.json or {}
    query         = data.get("message", "").strip()
    session_id    = data.get("session_id") or str(uuid.uuid4())
    customer_name = data.get("customer_name", "")

    if not query:
        return jsonify({"error": "message required"}), 400

    db    = get_db()
    venue = db.execute("SELECT name FROM venues WHERE id=?", (vid,)).fetchone()
    if not venue:
        return jsonify({"error": "Venue not found"}), 404

    # Build a compact menu snapshot for the AI context
    items = db.execute(
        "SELECT name, price, is_veg, is_vegan, tags "
        "FROM menu_items WHERE venue_id=? AND is_available=1 LIMIT 80",
        (vid,),
    ).fetchall()
    menu_ctx = "\n".join(
        f"- {i['name']} (₹{i['price']:.0f})"
        f"{'  [Veg]' if i['is_veg'] else ''}"
        f"{'  [Vegan]' if i['is_vegan'] else ''}"
        f" — {' '.join(json.loads(i['tags'])[:3])}"
        for i in items
    )

    # Load conversation history then append current message
    history_rows = db.execute(
        "SELECT role, content FROM chat_messages WHERE session_id=? ORDER BY created_at",
        (session_id,),
    ).fetchall()
    messages = [{"role": r["role"], "content": r["content"]} for r in history_rows]
    messages.append({"role": "user", "content": query})

    reply   = get_ai_response(messages, customer_name, menu_ctx)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for role, content in [("user", query), ("assistant", reply)]:
        db.execute(
            "INSERT INTO chat_messages (id, venue_id, session_id, role, content, created_at) "
            "VALUES (?,?,?,?,?,?)",
            (str(uuid.uuid4()), vid, session_id, role, content, now_str),
        )

    dishes = find_dishes(query, vid, top_k=3)
    db.commit()

    return jsonify({"session_id": session_id, "reply": reply, "suggested_dishes": dishes})


# ── orders ────────────────────────────────────────────────────────────────────

@public_bp.post("/venues/<vid>/orders")
def place_order(vid: str):
    data = request.json or {}

    if not data.get("order_type") or not data.get("items"):
        return jsonify({"error": "order_type and items required"}), 400

    db = get_db()
    if not db.execute("SELECT id FROM venues WHERE id=?", (vid,)).fetchone():
        return jsonify({"error": "Venue not found"}), 404

    # Validate and price every requested item
    order_items: list[dict] = []
    total = 0.0
    for it in data["items"]:
        row = db.execute(
            "SELECT id, name, price FROM menu_items WHERE id=? AND venue_id=? AND is_available=1",
            (it["id"], vid),
        ).fetchone()
        if not row:
            return jsonify({"error": f"Item not found: {it['id']}"}), 400
        qty    = max(1, int(it.get("quantity", 1)))
        price  = float(row["price"])
        total += price * qty
        order_items.append({"id": row["id"], "name": row["name"], "price": price, "qty": qty})

    dietary = data.get("dietary_pref", [])
    if isinstance(dietary, str):
        dietary = [dietary]

    now     = datetime.now()
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")
    oid     = str(uuid.uuid4())

    db.execute(
        """INSERT INTO orders
           (id, venue_id, customer_name, table_ref, order_type, spice_level,
            dietary_pref, portion_size, special_instructions, total_amount,
            status, created_at, hour_of_day, day_of_week)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            oid, vid,
            data.get("customer_name", "Guest"),
            data.get("table_ref", ""),
            data["order_type"],
            data.get("spice_level", "medium"),
            json.dumps(dietary),
            data.get("portion_size", "regular"),
            data.get("special_instructions", ""),
            round(total, 2),
            "pending",
            now_str,
            now.hour,
            now.strftime("%a"),
        ),
    )

    for it in order_items:
        db.execute(
            "INSERT INTO order_items (id, order_id, menu_item_id, name, price, quantity) "
            "VALUES (?,?,?,?,?,?)",
            (str(uuid.uuid4()), oid, it["id"], it["name"], it["price"], it["qty"]),
        )

    db.commit()
    return (
        jsonify(
            {
                "order_id": oid,
                "total":    round(total, 2),
                "status":   "pending",
                "message":  f"Order #{oid[:8].upper()} placed! We're on it ☕",
            }
        ),
        201,
    )
