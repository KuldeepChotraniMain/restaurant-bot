"""
routes/admin.py — password-protected admin endpoints
  POST   /api/admin/login
  GET    /api/admin/venues
  POST   /api/admin/venues
  DELETE /api/admin/venues/<vid>
  GET    /api/admin/venues/<vid>/categories
  POST   /api/admin/venues/<vid>/categories
  DELETE /api/admin/categories/<cid>
  GET    /api/admin/venues/<vid>/items
  POST   /api/admin/venues/<vid>/items
  PUT    /api/admin/items/<iid>
  DELETE /api/admin/items/<iid>
  GET    /api/admin/venues/<vid>/orders
  PUT    /api/admin/orders/<oid>/status
  GET    /api/admin/venues/<vid>/analytics
"""

import json
import uuid
from datetime import datetime
from functools import wraps

from flask import Blueprint, jsonify, request

from config import Config
from database import get_db

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


# ── auth guard ────────────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def require_admin(f):
    """Decorator: reject requests that don't carry the correct admin token."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.headers.get("X-Admin-Token") or request.args.get("token")
        if token != Config.ADMIN_PASSWORD:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return wrapper


# ── login ─────────────────────────────────────────────────────────────────────

@admin_bp.post("/login")
def admin_login():
    data = request.json or {}
    if data.get("password") == Config.ADMIN_PASSWORD:
        return jsonify({"token": Config.ADMIN_PASSWORD, "ok": True})
    return jsonify({"error": "Wrong password"}), 401


# ── venues ────────────────────────────────────────────────────────────────────

@admin_bp.get("/venues")
@require_admin
def admin_venues():
    rows = get_db().execute(
        "SELECT * FROM venues ORDER BY created_at DESC"
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@admin_bp.post("/venues")
@require_admin
def admin_add_venue():
    data = request.json or {}
    if not data.get("name") or not data.get("type"):
        return jsonify({"error": "name and type required"}), 400
    vid = str(uuid.uuid4())
    db  = get_db()
    db.execute(
        "INSERT INTO venues (id, name, type, description, address, created_at) VALUES (?,?,?,?,?,?)",
        (vid, data["name"], data["type"], data.get("description", ""), data.get("address", ""), _now()),
    )
    db.commit()
    return jsonify({"id": vid}), 201


@admin_bp.delete("/venues/<vid>")
@require_admin
def admin_delete_venue(vid: str):
    db = get_db()
    db.execute("DELETE FROM venues WHERE id=?", (vid,))
    db.commit()
    return jsonify({"ok": True})


# ── categories ────────────────────────────────────────────────────────────────

@admin_bp.get("/venues/<vid>/categories")
@require_admin
def admin_get_categories(vid: str):
    rows = get_db().execute(
        "SELECT * FROM categories WHERE venue_id=? ORDER BY sort_order", (vid,)
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@admin_bp.post("/venues/<vid>/categories")
@require_admin
def admin_add_category(vid: str):
    data = request.json or {}
    cid  = str(uuid.uuid4())
    db   = get_db()
    db.execute(
        "INSERT INTO categories (id, venue_id, name, sort_order) VALUES (?,?,?,?)",
        (cid, vid, data.get("name", "New Category"), data.get("sort_order", 0)),
    )
    db.commit()
    return jsonify({"id": cid}), 201


@admin_bp.delete("/categories/<cid>")
@require_admin
def admin_delete_category(cid: str):
    db = get_db()
    db.execute("DELETE FROM categories WHERE id=?", (cid,))
    db.commit()
    return jsonify({"ok": True})


# ── menu items ────────────────────────────────────────────────────────────────

@admin_bp.get("/venues/<vid>/items")
@require_admin
def admin_get_items(vid: str):
    rows = get_db().execute(
        """SELECT m.*, c.name AS category_name
           FROM menu_items m
           LEFT JOIN categories c ON m.category_id = c.id
           WHERE m.venue_id=?
           ORDER BY c.sort_order, m.name""",
        (vid,),
    ).fetchall()

    result = []
    for r in rows:
        d = dict(r)
        d["tags"]         = json.loads(d["tags"])
        d["is_veg"]       = bool(d["is_veg"])
        d["is_vegan"]     = bool(d["is_vegan"])
        d["is_available"] = bool(d["is_available"])
        result.append(d)
    return jsonify(result)


@admin_bp.post("/venues/<vid>/items")
@require_admin
def admin_add_item(vid: str):
    data = request.json or {}
    if not data.get("name") or data.get("price") is None:
        return jsonify({"error": "name and price required"}), 400
    iid = str(uuid.uuid4())
    db  = get_db()
    db.execute(
        """INSERT INTO menu_items
           (id, venue_id, category_id, name, description, price,
            is_veg, is_vegan, is_available, tags, created_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (
            iid, vid, data.get("category_id"),
            data["name"], data.get("description", ""),
            float(data["price"]),
            int(data.get("is_veg",  0)),
            int(data.get("is_vegan", 0)),
            1,
            json.dumps(data.get("tags", [])),
            _now(),
        ),
    )
    db.commit()
    return jsonify({"id": iid}), 201


@admin_bp.put("/items/<iid>")
@require_admin
def admin_update_item(iid: str):
    data = request.json or {}
    db   = get_db()
    db.execute(
        """UPDATE menu_items
           SET name=?, description=?, price=?, is_veg=?, is_vegan=?,
               is_available=?, tags=?, category_id=?
           WHERE id=?""",
        (
            data.get("name"),
            data.get("description", ""),
            float(data.get("price", 0)),
            int(data.get("is_veg",       0)),
            int(data.get("is_vegan",     0)),
            int(data.get("is_available", 1)),
            json.dumps(data.get("tags", [])),
            data.get("category_id"),
            iid,
        ),
    )
    db.commit()
    return jsonify({"ok": True})


@admin_bp.delete("/items/<iid>")
@require_admin
def admin_delete_item(iid: str):
    db = get_db()
    db.execute("DELETE FROM menu_items WHERE id=?", (iid,))
    db.commit()
    return jsonify({"ok": True})


# ── orders ────────────────────────────────────────────────────────────────────

@admin_bp.get("/venues/<vid>/orders")
@require_admin
def admin_orders(vid: str):
    db            = get_db()
    status_filter = request.args.get("status")
    query         = "SELECT * FROM orders WHERE venue_id=?"
    params        = [vid]

    if status_filter:
        query  += " AND status=?"
        params.append(status_filter)

    query += " ORDER BY created_at DESC LIMIT 100"
    rows   = db.execute(query, params).fetchall()

    result = []
    for r in rows:
        order                = dict(r)
        order["dietary_pref"] = json.loads(order["dietary_pref"])
        items                = db.execute(
            "SELECT name, price, quantity FROM order_items WHERE order_id=?", (r["id"],)
        ).fetchall()
        order["items"] = [dict(i) for i in items]
        result.append(order)

    return jsonify(result)


@admin_bp.put("/orders/<oid>/status")
@require_admin
def admin_update_order(oid: str):
    data = request.json or {}
    db   = get_db()
    db.execute("UPDATE orders SET status=? WHERE id=?", (data.get("status"), oid))
    db.commit()
    return jsonify({"ok": True})


# ── analytics ─────────────────────────────────────────────────────────────────

@admin_bp.get("/venues/<vid>/analytics")
@require_admin
def analytics(vid: str):
    db = get_db()

    hourly = db.execute(
        "SELECT hour_of_day, COUNT(*) AS count, ROUND(SUM(total_amount),2) AS revenue "
        "FROM orders WHERE venue_id=? GROUP BY hour_of_day ORDER BY hour_of_day",
        (vid,),
    ).fetchall()

    dow = db.execute(
        "SELECT day_of_week, COUNT(*) AS count FROM orders WHERE venue_id=? GROUP BY day_of_week",
        (vid,),
    ).fetchall()

    top_items = db.execute(
        """SELECT oi.name, SUM(oi.quantity) AS qty,
                  ROUND(SUM(oi.price * oi.quantity), 2) AS revenue
           FROM order_items oi
           JOIN orders o ON oi.order_id = o.id
           WHERE o.venue_id=?
           GROUP BY oi.name
           ORDER BY qty DESC
           LIMIT 10""",
        (vid,),
    ).fetchall()

    spice = db.execute(
        "SELECT spice_level, COUNT(*) AS count FROM orders "
        "WHERE venue_id=? AND spice_level IS NOT NULL GROUP BY spice_level",
        (vid,),
    ).fetchall()

    portions = db.execute(
        "SELECT portion_size, COUNT(*) AS count FROM orders "
        "WHERE venue_id=? AND portion_size IS NOT NULL GROUP BY portion_size",
        (vid,),
    ).fetchall()

    otype = db.execute(
        "SELECT order_type, COUNT(*) AS count FROM orders WHERE venue_id=? GROUP BY order_type",
        (vid,),
    ).fetchall()

    dietary_raw = db.execute(
        "SELECT dietary_pref FROM orders WHERE venue_id=?", (vid,)
    ).fetchall()
    diet_counts: dict[str, int] = {}
    for row in dietary_raw:
        for pref in json.loads(row["dietary_pref"]):
            diet_counts[pref] = diet_counts.get(pref, 0) + 1

    stats = db.execute(
        """SELECT
             COUNT(*) AS total_orders,
             SUM(CASE WHEN status='completed'  THEN 1 ELSE 0 END) AS completed,
             SUM(CASE WHEN status='pending'    THEN 1 ELSE 0 END) AS pending,
             SUM(CASE WHEN status='preparing'  THEN 1 ELSE 0 END) AS preparing,
             ROUND(AVG(total_amount), 2) AS avg_order_value,
             ROUND(SUM(total_amount), 2) AS total_revenue
           FROM orders WHERE venue_id=?""",
        (vid,),
    ).fetchone()

    return jsonify(
        {
            "stats":         dict(stats),
            "hourly":        [dict(r) for r in hourly],
            "day_of_week":   [dict(r) for r in dow],
            "top_items":     [dict(r) for r in top_items],
            "spice_prefs":   [dict(r) for r in spice],
            "portion_prefs": [dict(r) for r in portions],
            "order_types":   [dict(r) for r in otype],
            "dietary_prefs": sorted(diet_counts.items(), key=lambda x: -x[1]),
        }
    )
