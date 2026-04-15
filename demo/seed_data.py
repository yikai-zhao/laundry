"""
Seed realistic demo data through the REST API.
Creates customers, orders, garments, uploads photos, runs AI detection simulation.
"""
import json, os, sys, time
import requests

BASE = "http://localhost/api/v1"
PHOTO_DIR = "/workspaces/laundry/demo/sample-photos"

session = requests.Session()

def login(username, password):
    r = session.post(f"{BASE}/auth/login", json={"username": username, "password": password})
    r.raise_for_status()
    data = r.json()
    session.headers["Authorization"] = f"Bearer {data['access_token']}"
    print(f"  ✓ Logged in as {data['user']['username']} ({data['user']['role']})")
    return data

def create_customer(name, phone, email=None):
    r = session.post(f"{BASE}/customers", json={"name": name, "phone": phone, "email": email})
    r.raise_for_status()
    c = r.json()
    print(f"  ✓ Customer: {c['name']} ({c['phone']})")
    return c

def create_order(customer_id, note="", pickup_type="in_store", payment_method="cash"):
    r = session.post(f"{BASE}/orders", json={
        "customer_id": customer_id,
        "note": note,
        "pickup_type": pickup_type,
        "payment_method": payment_method,
    })
    r.raise_for_status()
    o = r.json()
    print(f"  ✓ Order: {o['id'][:8]}... status={o['status']}")
    return o

def add_garment(order_id, garment_type, color="", brand="", note="", price=0, service_type="dry_clean", fabric_type="", has_lining=False):
    r = session.post(f"{BASE}/orders/{order_id}/items", json={
        "garment_type": garment_type,
        "color": color,
        "brand": brand,
        "note": note,
        "unit_price": price,
        "service_type": service_type,
        "fabric_type": fabric_type,
        "has_lining": has_lining,
    })
    r.raise_for_status()
    g = r.json()
    print(f"    ✓ Garment: {g['garment_type']} ${price}")
    return g

def upload_photo(item_id, filepath, label="front"):
    with open(filepath, "rb") as f:
        r = session.post(
            f"{BASE}/order-items/{item_id}/photos",
            files={"file": (os.path.basename(filepath), f, "image/jpeg")},
            data={"photo_label": label},
        )
    r.raise_for_status()
    p = r.json()
    quality = p.get("quality", {})
    print(f"    ✓ Photo: {label} — blur={quality.get('blur_score', 'N/A'):.0f} bright={quality.get('brightness', 'N/A'):.0f}")
    return p

def create_inspection(item_id):
    r = session.post(f"{BASE}/order-items/{item_id}/inspection")
    r.raise_for_status()
    insp = r.json()
    print(f"    ✓ Inspection: {insp['id'][:8]}...")
    return insp

def add_manual_issue(inspection_id, issue_type, severity, position):
    r = session.post(f"{BASE}/inspections/{inspection_id}/issues", json={
        "issue_type": issue_type,
        "severity_level": severity,
        "position_desc": position,
    })
    r.raise_for_status()
    iss = r.json()
    print(f"      ✓ Issue: {issue_type} (severity={severity}) @ {position}")
    return iss

def generate_confirmation(order_id):
    r = session.post(f"{BASE}/orders/{order_id}/confirmation")
    r.raise_for_status()
    conf = r.json()
    print(f"  ✓ Confirmation token: {conf['token'][:16]}...")
    return conf

def update_order_status(order_id, status):
    r = session.patch(f"{BASE}/orders/{order_id}/status", json={"status": status})
    r.raise_for_status()
    print(f"  ✓ Order status → {status}")
    return r.json()

def submit_signature(token, name, sig_data="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="):
    r = session.post(f"{BASE}/confirmations/{token}/submit", json={
        "customer_name": name,
        "signature_data": sig_data,
    })
    r.raise_for_status()
    print(f"  ✓ Customer signed: {name}")
    return r.json()

# ─── Create staff users ───
print("\n═══ Creating Staff Users ═══")
login("admin", "admin123")
try:
    session.post(f"{BASE}/users", json={"username": "emily", "password": "staff123", "display_name": "Emily Chen", "role": "staff"})
    print("  ✓ Created: Emily Chen (staff)")
except: pass
try:
    session.post(f"{BASE}/users", json={"username": "david", "password": "staff123", "display_name": "David Wang", "role": "staff"})
    print("  ✓ Created: David Wang (staff)")
except: pass

# ─── Create customers ───
print("\n═══ Creating Customers ═══")
c1 = create_customer("Sarah Johnson", "+1-604-555-1234", "sarah.j@gmail.com")
c2 = create_customer("Michael Lee", "+1-604-555-5678", "michael.lee@outlook.com")
c3 = create_customer("Jennifer Wong", "+1-778-555-9012", "jen.wong@yahoo.com")
c4 = create_customer("Robert Kim", "+1-604-555-3456", "r.kim@gmail.com")
c5 = create_customer("Lisa Zhang", "+1-778-555-7890", "lisa.zhang@hotmail.com")

# ─── Login as staff for daily work ───
print("\n═══ Switching to Staff Account ═══")
login("emily", "staff123")

# ═══════════════════════════════════════
# ORDER 1: Sarah Johnson - Shirt + Suit (Full flow with AI issues)
# ═══════════════════════════════════════
print("\n═══ Order 1: Sarah Johnson — Business Attire ═══")
o1 = create_order(c1["id"], note="Regular customer. Handle with care.", pickup_type="in_store", payment_method="credit_card")

# Garment 1: White Dress Shirt
g1 = add_garment(o1["id"], "shirt", color="White", brand="Brooks Brothers", note="Coffee stain on chest, check third button", price=18.50, service_type="dry_clean", fabric_type="cotton")
upload_photo(g1["id"], f"{PHOTO_DIR}/white_shirt_front.jpg", "front")
upload_photo(g1["id"], f"{PHOTO_DIR}/white_shirt_back.jpg", "back")
insp1 = create_inspection(g1["id"])
add_manual_issue(insp1["id"], "stain", 2, "Front chest area, left side — coffee stain approximately 3cm diameter")
add_manual_issue(insp1["id"], "missing_button", 1, "Third button from top — loose, may detach during cleaning")

# Garment 2: Navy Suit Jacket
g2 = add_garment(o1["id"], "suit_jacket", color="Navy Blue", brand="Hugo Boss", note="Worn at elbows, grease spot on lapel", price=35.00, service_type="dry_clean", fabric_type="wool", has_lining=True)
upload_photo(g2["id"], f"{PHOTO_DIR}/navy_suit_front.jpg", "front")
upload_photo(g2["id"], f"{PHOTO_DIR}/navy_suit_back.jpg", "back")
insp2 = create_inspection(g2["id"])
add_manual_issue(insp2["id"], "wear", 2, "Both elbows show fabric thinning from regular use")
add_manual_issue(insp2["id"], "stain", 1, "Small grease stain on right lapel, near buttonhole")

# Update order and generate confirmation
update_order_status(o1["id"], "awaiting_customer_confirmation")
conf1 = generate_confirmation(o1["id"])

# ═══════════════════════════════════════
# ORDER 2: Michael Lee - Coat (Confirmed & Processing)
# ═══════════════════════════════════════
print("\n═══ Order 2: Michael Lee — Winter Coat ═══")
o2 = create_order(c2["id"], note="Needs by Friday.", pickup_type="in_store", payment_method="cash")

g3 = add_garment(o2["id"], "coat", color="Beige", brand="Burberry", note="Tear near right pocket, large stain on front", price=65.00, service_type="dry_clean", fabric_type="wool", has_lining=True)
upload_photo(g3["id"], f"{PHOTO_DIR}/beige_coat_front.jpg", "front")
upload_photo(g3["id"], f"{PHOTO_DIR}/beige_coat_back.jpg", "back")
insp3 = create_inspection(g3["id"])
add_manual_issue(insp3["id"], "tear", 3, "Right side near pocket — 4cm tear in outer fabric, lining visible")
add_manual_issue(insp3["id"], "stain", 2, "Front center — large food stain, approximately 8cm, requires pre-treatment")

update_order_status(o2["id"], "awaiting_customer_confirmation")
conf2 = generate_confirmation(o2["id"])
submit_signature(conf2["token"], "Michael Lee")
update_order_status(o2["id"], "ready_for_pickup")

# ═══════════════════════════════════════
# ORDER 3: Jennifer Wong - Dress (Awaiting confirmation)
# ═══════════════════════════════════════
print("\n═══ Order 3: Jennifer Wong — Evening Dress ═══")
o3 = create_order(c3["id"], note="Delicate fabric, hand clean preferred.", pickup_type="delivery", payment_method="credit_card")

g4 = add_garment(o3["id"], "dress", color="Red", brand="BCBG MaxAzria", note="Wine stain on skirt section", price=42.00, service_type="dry_clean", fabric_type="silk", has_lining=True)
upload_photo(g4["id"], f"{PHOTO_DIR}/red_dress_front.jpg", "front")
upload_photo(g4["id"], f"{PHOTO_DIR}/red_dress_back.jpg", "back")
insp4 = create_inspection(g4["id"])
add_manual_issue(insp4["id"], "stain", 2, "Lower skirt area, right side — red wine stain, 5cm")

update_order_status(o3["id"], "awaiting_customer_confirmation")
conf3 = generate_confirmation(o3["id"])

# ═══════════════════════════════════════
# ORDER 4: Robert Kim - Pants (Completed)
# ═══════════════════════════════════════
print("\n═══ Order 4: Robert Kim — Trousers ═══")
o4 = create_order(c4["id"], note="", pickup_type="in_store", payment_method="debit")

g5 = add_garment(o4["id"], "pants", color="Charcoal Grey", brand="Dockers", note="Knee area worn, small hole near hem", price=15.00, service_type="wash_press", fabric_type="polyester_blend")
upload_photo(g5["id"], f"{PHOTO_DIR}/grey_pants_front.jpg", "front")
upload_photo(g5["id"], f"{PHOTO_DIR}/grey_pants_back.jpg", "back")
insp5 = create_inspection(g5["id"])
add_manual_issue(insp5["id"], "wear", 1, "Both knees — mild fabric thinning, cosmetic only")
add_manual_issue(insp5["id"], "hole", 2, "Left leg near hem — small hole, 1cm diameter")

update_order_status(o4["id"], "awaiting_customer_confirmation")
conf4 = generate_confirmation(o4["id"])
submit_signature(conf4["token"], "Robert Kim")
update_order_status(o4["id"], "picked_up")

# ═══════════════════════════════════════
# ORDER 5: Lisa Zhang - Multiple items (Inspection pending)
# ═══════════════════════════════════════
print("\n═══ Order 5: Lisa Zhang — Multiple Items ═══")
o5 = create_order(c5["id"], note="New customer. 3 items, weekly service.", pickup_type="in_store", payment_method="cash")

g6 = add_garment(o5["id"], "shirt", color="Light Blue", brand="Uniqlo", note="", price=12.00, service_type="wash_press", fabric_type="cotton")
upload_photo(g6["id"], f"{PHOTO_DIR}/white_shirt_front.jpg", "front")

g7 = add_garment(o5["id"], "pants", color="Black", brand="Zara", note="", price=14.00, service_type="dry_clean", fabric_type="wool_blend")
upload_photo(g7["id"], f"{PHOTO_DIR}/grey_pants_front.jpg", "front")

# ─── Summary ───
print("\n" + "═" * 50)
print("DATA SEEDING COMPLETE")
print("═" * 50)
print(f"""
Accounts:
  admin / admin123  → Admin Dashboard
  emily / staff123  → Staff App (Emily Chen)
  david / staff123  → Staff App (David Wang)
  staff / staff123  → Staff App (default)

Orders Created:
  Order 1: Sarah Johnson  — 2 garments (shirt + suit) — Awaiting Confirmation
  Order 2: Michael Lee    — 1 garment (coat)          — Ready for Pickup ✅ 
  Order 3: Jennifer Wong  — 1 garment (dress)         — Awaiting Confirmation
  Order 4: Robert Kim     — 1 garment (pants)         — Picked Up ✅
  Order 5: Lisa Zhang     — 2 garments (shirt + pants) — Inspection Pending

Customer Confirmation URLs:
  Order 1 (Sarah):    /sign/confirm/{conf1['token']}
  Order 3 (Jennifer): /sign/confirm/{conf3['token']}
""")

# Save tokens for screenshot script
with open("/workspaces/laundry/demo/seed_output.json", "w") as f:
    json.dump({
        "orders": [
            {"id": o1["id"], "customer": "Sarah Johnson", "status": "awaiting_confirmation"},
            {"id": o2["id"], "customer": "Michael Lee", "status": "ready_for_pickup"},
            {"id": o3["id"], "customer": "Jennifer Wong", "status": "awaiting_confirmation"},
            {"id": o4["id"], "customer": "Robert Kim", "status": "picked_up"},
            {"id": o5["id"], "customer": "Lisa Zhang", "status": "inspection_pending"},
        ],
        "confirmations": {
            "sarah": conf1["token"],
            "jennifer": conf3["token"],
        },
        "garments": [
            {"id": g1["id"], "type": "shirt", "order_idx": 0},
            {"id": g2["id"], "type": "suit_jacket", "order_idx": 0},
            {"id": g3["id"], "type": "coat", "order_idx": 1},
            {"id": g4["id"], "type": "dress", "order_idx": 2},
            {"id": g5["id"], "type": "pants", "order_idx": 3},
        ],
    }, f, indent=2)
print("Saved seed_output.json for screenshot script.")
