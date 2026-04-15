"""
Seed demo data with realistic AI-detection results.
All issues include bbox coordinates, confidence scores, and AI source attribution.
"""
import json, os, sys, time, requests

BASE = "http://localhost/api/v1"
PHOTO_DIR = "/workspaces/laundry/demo/sample-photos"
session = requests.Session()

def login(u, p):
    r = session.post(f"{BASE}/auth/login", json={"username": u, "password": p})
    r.raise_for_status()
    d = r.json(); session.headers["Authorization"] = f"Bearer {d['access_token']}"
    print(f"  ✓ Logged in as {d['user']['username']}")
    return d

def customer(name, phone, email=None):
    r = session.post(f"{BASE}/customers", json={"name": name, "phone": phone, "email": email})
    r.raise_for_status(); c = r.json(); print(f"  ✓ Customer: {c['name']}"); return c

def order(cid, note="", pickup="in_store", pay="cash"):
    r = session.post(f"{BASE}/orders", json={"customer_id": cid, "note": note, "pickup_type": pickup, "payment_method": pay})
    r.raise_for_status(); o = r.json(); print(f"  ✓ Order: {o['id'][:8]}..."); return o

def garment(oid, gtype, **kw):
    body = {"garment_type": gtype, "color": kw.get("color",""), "brand": kw.get("brand",""),
            "note": kw.get("note",""), "unit_price": kw.get("price",0),
            "service_type": kw.get("svc","dry_clean"), "fabric_type": kw.get("fabric",""),
            "has_lining": kw.get("lining",False)}
    r = session.post(f"{BASE}/orders/{oid}/items", json=body)
    r.raise_for_status(); g = r.json(); print(f"    ✓ Garment: {g['garment_type']} ${kw.get('price',0)}"); return g

def photo(item_id, path, label="front"):
    with open(path, "rb") as f:
        r = session.post(f"{BASE}/order-items/{item_id}/photos",
                         files={"file": (os.path.basename(path), f, "image/jpeg")},
                         data={"photo_label": label})
    r.raise_for_status(); print(f"    ✓ Photo: {label}"); return r.json()

def inspection(item_id):
    r = session.post(f"{BASE}/order-items/{item_id}/inspection")
    r.raise_for_status(); insp = r.json(); print(f"    ✓ Inspection: {insp['id'][:8]}..."); return insp

def ai_issue(insp_id, itype, sev, pos, conf, bx, by, bw, bh):
    """Add issue as AI-detected with full bbox + confidence."""
    r = session.post(f"{BASE}/inspections/{insp_id}/issues", json={
        "issue_type": itype, "severity_level": sev, "position_desc": pos,
        "confidence_score": conf, "bbox_x": bx, "bbox_y": by, "bbox_w": bw, "bbox_h": bh,
        "source": "ai",
    })
    r.raise_for_status()
    print(f"      ✓ AI Issue: {itype} S{sev} conf={conf:.0%} @ [{bx:.2f},{by:.2f},{bw:.2f},{bh:.2f}]")
    return r.json()

def manual_issue(insp_id, itype, sev, pos):
    """Add a manual issue (staff added after AI review)."""
    r = session.post(f"{BASE}/inspections/{insp_id}/issues", json={
        "issue_type": itype, "severity_level": sev, "position_desc": pos, "source": "manual",
    })
    r.raise_for_status(); print(f"      ✓ Manual Issue: {itype} S{sev}"); return r.json()

def confirmation(oid):
    r = session.post(f"{BASE}/orders/{oid}/confirmation")
    r.raise_for_status(); c = r.json(); print(f"  ✓ Confirmation: {c['token'][:16]}..."); return c

def status(oid, s):
    r = session.patch(f"{BASE}/orders/{oid}/status", json={"status": s})
    r.raise_for_status(); print(f"  ✓ Status → {s}"); return r.json()

def sign(token, name):
    r = session.post(f"{BASE}/confirmations/{token}/submit", json={
        "customer_name": name,
        "signature_data": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
    })
    r.raise_for_status(); print(f"  ✓ Signed by: {name}"); return r.json()

# ─── Reset DB ───
print("\n═══ Reset Database ═══")
login("admin", "admin123")
try:
    session.post(f"{BASE}/users", json={"username":"emily","password":"staff123","display_name":"Emily Chen","role":"staff"})
    print("  ✓ Created: Emily Chen")
except: pass
try:
    session.post(f"{BASE}/users", json={"username":"david","password":"staff123","display_name":"David Wang","role":"staff"})
    print("  ✓ Created: David Wang")
except: pass

# ─── Customers ───
print("\n═══ Customers ═══")
c1 = customer("Sarah Johnson", "+1-604-555-1234", "sarah.j@gmail.com")
c2 = customer("Michael Lee", "+1-604-555-5678", "michael.lee@outlook.com")
c3 = customer("Jennifer Wong", "+1-778-555-9012", "jen.wong@yahoo.com")
c4 = customer("Robert Kim", "+1-604-555-3456", "r.kim@gmail.com")
c5 = customer("Lisa Zhang", "+1-778-555-7890", "lisa.zhang@hotmail.com")

login("emily", "staff123")

# ═══════════════════════════════════════
# ORDER 1: Sarah Johnson — Business Attire (2 garments, AI-detected issues)
# This is the SHOWCASE order for AI demo
# ═══════════════════════════════════════
print("\n═══ Order 1: Sarah Johnson — 🤖 AI Showcase ═══")
o1 = order(c1["id"], note="Regular customer. Handle with care.", pickup="in_store", pay="credit_card")

# Garment 1: White Dress Shirt — AI detects stain + missing button
g1 = garment(o1["id"], "shirt", color="White", brand="Brooks Brothers",
             note="Coffee stain on chest, check third button", price=18.50,
             svc="dry_clean", fabric="Cotton")
photo(g1["id"], f"{PHOTO_DIR}/white_shirt_front.jpg", "front")
photo(g1["id"], f"{PHOTO_DIR}/white_shirt_back.jpg", "back")
insp1 = inspection(g1["id"])

# AI-detected: coffee stain on front chest (high confidence)
ai_issue(insp1["id"], "stain", 2,
         "Front chest area, left side — coffee stain approximately 3cm diameter, brown discoloration on white fabric",
         0.94, 0.35, 0.30, 0.15, 0.12)

# AI-detected: missing button
ai_issue(insp1["id"], "missing_button", 1,
         "Third button from top — button loose, thread visibly frayed, risk of detachment during cleaning",
         0.87, 0.42, 0.48, 0.08, 0.06)

# AI-detected: mild wear at collar
ai_issue(insp1["id"], "wear", 1,
         "Collar edge — mild fraying along fold line, consistent with regular wear",
         0.72, 0.30, 0.05, 0.20, 0.08)

# Staff manually adds: small ink mark AI missed
manual_issue(insp1["id"], "stain", 1,
             "Right cuff, inner side — small blue ink mark, 5mm, barely visible")

# Garment 2: Navy Suit Jacket — AI detects wear + stain
g2 = garment(o1["id"], "suit_jacket", color="Navy Blue", brand="Hugo Boss",
             note="Worn at elbows, grease spot on lapel", price=35.00,
             svc="dry_clean", fabric="Wool", lining=True)
photo(g2["id"], f"{PHOTO_DIR}/navy_suit_front.jpg", "front")
photo(g2["id"], f"{PHOTO_DIR}/navy_suit_back.jpg", "back")
insp2 = inspection(g2["id"])

# AI-detected: elbow wear (both sides)
ai_issue(insp2["id"], "wear", 2,
         "Both elbows — fabric thinning and slight pilling from regular use, left elbow more pronounced",
         0.91, 0.10, 0.40, 0.25, 0.18)

# AI-detected: grease stain on lapel
ai_issue(insp2["id"], "stain", 1,
         "Right front lapel, near buttonhole — small grease/oil stain, approximately 1cm, translucent mark",
         0.83, 0.55, 0.20, 0.10, 0.08)

# AI-detected: pilling on back
ai_issue(insp2["id"], "pilling", 1,
         "Upper back between shoulders — light pilling across a 10cm area, common in wool blend",
         0.76, 0.30, 0.15, 0.40, 0.20)

status(o1["id"], "awaiting_customer_confirmation")
conf1 = confirmation(o1["id"])

# ═══════════════════════════════════════
# ORDER 2: Michael Lee — Winter Coat (severe tear + stain, AI + manual)
# ═══════════════════════════════════════
print("\n═══ Order 2: Michael Lee — Heavy Damage Detection ═══")
o2 = order(c2["id"], note="Needs by Friday. Expensive coat.", pickup="in_store", pay="cash")

g3 = garment(o2["id"], "coat", color="Beige", brand="Burberry",
             note="Tear near right pocket, large stain on front", price=85.00,
             svc="luxury_care", fabric="Wool/Cashmere", lining=True)
photo(g3["id"], f"{PHOTO_DIR}/beige_coat_front.jpg", "front")
photo(g3["id"], f"{PHOTO_DIR}/beige_coat_back.jpg", "back")
insp3 = inspection(g3["id"])

# AI-detected: severe tear (high confidence)
ai_issue(insp3["id"], "tear", 3,
         "Right side near pocket — 4cm tear through outer fabric, inner lining exposed. Needs repair before cleaning.",
         0.97, 0.65, 0.55, 0.12, 0.15)

# AI-detected: large food stain
ai_issue(insp3["id"], "stain", 2,
         "Front center chest — large food stain approximately 8cm diameter, appears to be sauce/grease, requires pre-treatment",
         0.95, 0.30, 0.25, 0.25, 0.20)

# AI-detected: fading at shoulders
ai_issue(insp3["id"], "fade", 1,
         "Both shoulders — sun fading, slight colour difference between shoulder top and body",
         0.68, 0.20, 0.02, 0.60, 0.10)

# Staff adds: lining damage AI couldn't see
manual_issue(insp3["id"], "tear", 2,
             "Inner lining, left chest pocket area — seam splitting 6cm, not visible from outside")

status(o2["id"], "awaiting_customer_confirmation")
conf2 = confirmation(o2["id"])
sign(conf2["token"], "Michael Lee")
status(o2["id"], "ready_for_pickup")

# ═══════════════════════════════════════
# ORDER 3: Jennifer Wong — Evening Dress (delicate fabric detection)
# ═══════════════════════════════════════
print("\n═══ Order 3: Jennifer Wong — Delicate Fabric AI ═══")
o3 = order(c3["id"], note="Delicate fabric, hand clean preferred.", pickup="delivery", pay="credit_card")

g4 = garment(o3["id"], "dress", color="Red", brand="BCBG MaxAzria",
             note="Wine stain on skirt section", price=55.00,
             svc="luxury_care", fabric="Silk", lining=True)
photo(g4["id"], f"{PHOTO_DIR}/red_dress_front.jpg", "front")
photo(g4["id"], f"{PHOTO_DIR}/red_dress_back.jpg", "back")
insp4 = inspection(g4["id"])

# AI-detected: wine stain
ai_issue(insp4["id"], "stain", 2,
         "Lower skirt area, right side — red wine stain approximately 5cm, partially set into silk fabric, needs gentle solvent treatment",
         0.92, 0.55, 0.65, 0.18, 0.15)

# AI-detected: pulled thread
ai_issue(insp4["id"], "tear", 1,
         "Left shoulder strap — single pulled thread, minor but may worsen if not addressed before agitation",
         0.79, 0.15, 0.08, 0.10, 0.05)

# AI-detected: wrinkle pattern
ai_issue(insp4["id"], "wrinkle", 1,
         "Back mid-section — set-in wrinkle lines from storage, silk will need careful steaming",
         0.71, 0.25, 0.35, 0.50, 0.25)

status(o3["id"], "awaiting_customer_confirmation")
conf3 = confirmation(o3["id"])

# ═══════════════════════════════════════
# ORDER 4: Robert Kim — Trousers (completed)
# ═══════════════════════════════════════
print("\n═══ Order 4: Robert Kim — Completed Order ═══")
o4 = order(c4["id"], note="", pickup="in_store", pay="debit")

g5 = garment(o4["id"], "pants", color="Charcoal Grey", brand="Dockers",
             note="Knee area worn, small hole near hem", price=15.00,
             svc="wash_press", fabric="Polyester Blend")
photo(g5["id"], f"{PHOTO_DIR}/grey_pants_front.jpg", "front")
photo(g5["id"], f"{PHOTO_DIR}/grey_pants_back.jpg", "back")
insp5 = inspection(g5["id"])

ai_issue(insp5["id"], "wear", 1,
         "Both knees — mild fabric thinning, cosmetic only, no structural damage",
         0.82, 0.30, 0.50, 0.40, 0.15)
ai_issue(insp5["id"], "hole", 2,
         "Left leg near hem — small hole 1cm diameter, edges frayed, recommend repair patch",
         0.90, 0.20, 0.85, 0.08, 0.08)

status(o4["id"], "awaiting_customer_confirmation")
conf4 = confirmation(o4["id"])
sign(conf4["token"], "Robert Kim")
status(o4["id"], "picked_up")

# ═══════════════════════════════════════
# ORDER 5: Lisa Zhang — Multiple items (inspection in progress)
# ═══════════════════════════════════════
print("\n═══ Order 5: Lisa Zhang — In Progress ═══")
o5 = order(c5["id"], note="New customer. 3 items, weekly service.", pickup="in_store", pay="cash")

g6 = garment(o5["id"], "shirt", color="Light Blue", brand="Uniqlo", price=12.00,
             svc="wash_press", fabric="Cotton")
photo(g6["id"], f"{PHOTO_DIR}/white_shirt_front.jpg", "front")

g7 = garment(o5["id"], "pants", color="Black", brand="Zara", price=14.00,
             svc="dry_clean", fabric="Wool Blend")
photo(g7["id"], f"{PHOTO_DIR}/grey_pants_front.jpg", "front")

# ─── Summary ───
print("\n" + "═" * 50)
print("AI DEMO DATA SEEDING COMPLETE")
print("═" * 50)
print(f"""
Orders:
  1. Sarah Johnson  — 2 garments, 7 issues (6 AI + 1 manual) — Awaiting Sig
  2. Michael Lee    — 1 garment, 4 issues (3 AI + 1 manual) — Ready Pickup
  3. Jennifer Wong  — 1 garment, 3 issues (3 AI)             — Awaiting Sig
  4. Robert Kim     — 1 garment, 2 issues (2 AI)             — Picked Up
  5. Lisa Zhang     — 2 garments, no inspection yet           — Created

Total: 16 AI-detected issues with bounding boxes + 2 staff manual additions
""")

with open("/workspaces/laundry/demo/seed_output.json", "w") as f:
    json.dump({
        "orders": [
            {"id": o1["id"], "customer": "Sarah Johnson", "status": "awaiting_confirmation"},
            {"id": o2["id"], "customer": "Michael Lee", "status": "ready_for_pickup"},
            {"id": o3["id"], "customer": "Jennifer Wong", "status": "awaiting_confirmation"},
            {"id": o4["id"], "customer": "Robert Kim", "status": "picked_up"},
            {"id": o5["id"], "customer": "Lisa Zhang", "status": "created"},
        ],
        "confirmations": {"sarah": conf1["token"], "jennifer": conf3["token"]},
        "garments": [
            {"id": g1["id"], "type": "shirt"},
            {"id": g2["id"], "type": "suit_jacket"},
            {"id": g3["id"], "type": "coat"},
            {"id": g4["id"], "type": "dress"},
        ],
    }, f, indent=2)
    print("  ✓ Saved seed_output.json")
