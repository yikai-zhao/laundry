"""
Live detection test for uploaded garment photos.
Drop photos into /workspaces/laundry/tmp/test/ then run:
  cd /workspaces/laundry && python3 tmp/test/run_test.py
"""
import requests, time, json, os, sys

BASE = "http://localhost:8000/api/v1"
PHOTO_DIR = os.path.dirname(__file__)

TEST_CASES = [
    # (filename, garment_type, color, expected_description)
    ("coat.jpg",    "Suede Coat",       "Beige",  "stain at collar seam"),
    ("leather.jpg", "Leather Jacket",   "Gray",   "widespread stain on front panel"),
    ("shoes.jpg",   "Sneakers",         "White",  "yellowing + grime on toe box"),
    ("down.jpg",    "Down Jacket",      "Yellow", "stain near pocket panel"),
]

def run():
    # Login
    r = requests.post(f"{BASE}/auth/login", json={"username": "admin", "password": "admin123"})
    token = r.json()["access_token"]
    H = {"Authorization": f"Bearer {token}"}

    # Get first customer
    customers = requests.get(f"{BASE}/customers?limit=1", headers=H).json()
    customer_id = customers[0]["id"]

    results = []
    for fname, garment_type, color, expected in TEST_CASES:
        fpath = os.path.join(PHOTO_DIR, fname)
        if not os.path.exists(fpath):
            print(f"SKIP {fname} — file not found")
            continue

        print(f"\n{'='*55}")
        print(f"Testing: {fname} ({garment_type})")
        print(f"Expected: {expected}")

        # Create order + item + inspection
        order_id = requests.post(f"{BASE}/orders", headers=H,
            json={"customer_id": customer_id, "notes": f"live test - {fname}"}).json()["id"]
        item_id = requests.post(f"{BASE}/orders/{order_id}/items", headers=H,
            json={"garment_type": garment_type, "service_type": "Wash", "color": color, "brand": ""}).json()["id"]
        insp_id = requests.post(f"{BASE}/order-items/{item_id}/inspection", headers=H).json()["id"]

        # Upload photo
        with open(fpath, "rb") as f:
            requests.post(f"{BASE}/order-items/{item_id}/photos", headers=H,
                          files={"file": (fname, f, "image/jpeg")})

        # Trigger detection
        requests.post(f"{BASE}/inspections/{insp_id}/detect", headers=H)
        print(f"Detection started (inspection={insp_id})...")

        # Poll
        for i in range(60):
            time.sleep(5)
            data = requests.get(f"{BASE}/inspections/{insp_id}", headers=H).json()
            if data["status"] != "detecting":
                issues = data.get("issues", [])
                print(f"  → {len(issues)} issues found after {(i+1)*5}s")
                for iss in issues:
                    print(f"     [{iss['issue_type']}] sev={iss['severity_level']} conf={iss['confidence_score']:.2f} | {iss['position_desc']}")
                results.append({"file": fname, "issues": len(issues), "data": issues})
                break
            sys.stdout.write(f"\r  polling... {(i+1)*5}s")
            sys.stdout.flush()

    print(f"\n\n{'='*55}")
    print(f"SUMMARY: {len(results)} garments tested")
    for r2 in results:
        print(f"  {r2['file']}: {r2['issues']} issues")

if __name__ == "__main__":
    run()
