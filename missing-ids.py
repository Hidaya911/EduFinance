"""
One-time repair script for EduFinance / djongo + MongoDB Atlas.

WHY THIS EXISTS
----------------
djongo emulates Django's integer AutoField ("id") on top of MongoDB, which
has no native auto-increment. That emulation is unreliable: documents
created via certain paths (createsuperuser, Django's own default Group
seeding, etc.) sometimes end up with only Mongo's `_id` (ObjectId) and no
`id` field at all. Anywhere Django needs that `id` — sessions, foreign
keys, url reversing with an object's .pk/.id, role_permissions links,
etc. — you get errors like:

    ValueError: Field 'id' expected a number but got 'None'.
    ValidationError: ["'None' value must be an integer."]

You've now hit this on auth_user AND auth_group. This script scans every
collection in the database and assigns a sequential integer `id` to any
document that's missing one, without touching anything that already has
a valid id.

USAGE
-----
1. Place this file in your project root (same folder as manage.py).
2. Make sure MONGO_URI is set — either already in your environment/.env,
   or paste it directly into MONGO_URI below.
3. Run:
       python fix_missing_ids.py
4. Read the printed report. Restart your Django server afterwards.

This only ADDS a field where missing. It never deletes or overwrites an
existing id, and never touches any other field.
"""

import os
from pymongo import MongoClient, ASCENDING

# Load variables from your .env file the same way settings.py does.
# Without this, MONGO_URI would only be found if it happens to already be
# set as a real OS environment variable — which is why the first run of
# this script printed "Nothing to fix" (it silently connected to nothing).
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("WARNING: python-dotenv not installed — MONGO_URI must already "
          "be set as a real environment variable for this to work.")

MONGO_URI = os.environ.get("MONGO_URI") or "PASTE_YOUR_MONGO_URI_HERE"
DB_NAME = os.environ.get("MONGO_DB_NAME") or "edufinance"


def main():
    if MONGO_URI == "PASTE_YOUR_MONGO_URI_HERE":
        print("ERROR: MONGO_URI was not found in your environment or .env "
              "file. Paste your connection string directly into the "
              "MONGO_URI line near the top of this script and run it "
              "again.")
        return

    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]

    # Diagnostics first — prove we're actually looking at the real data
    # before claiming anything is or isn't fixed.
    masked_uri = MONGO_URI.split('@')[-1] if '@' in MONGO_URI else MONGO_URI
    print(f"Connected to database: {DB_NAME}  (host: ...@{masked_uri})")
    collection_names = sorted(db.list_collection_names())
    print(f"Found {len(collection_names)} collection(s):")
    for name in collection_names:
        count = db[name].estimated_document_count()
        print(f"  - {name}: {count} document(s)")
    print()

    total_fixed = 0
    collections_touched = 0

    for collection_name in collection_names:
        if collection_name.startswith("system."):
            continue

        collection = db[collection_name]

        # Continue numbering after whatever the highest existing id is,
        # so we never collide with an id that's already correct.
        highest = collection.find_one(
            {"id": {"$exists": True, "$type": "int"}},
            sort=[("id", -1)],
        )
        next_id = (highest["id"] + 1) if highest else 1

        missing = list(
            collection.find({"id": {"$exists": False}}).sort("_id", ASCENDING)
        )

        if not missing:
            continue

        collections_touched += 1
        print(f"{collection_name}: {len(missing)} document(s) missing 'id' "
              f"-> assigning {next_id}..{next_id + len(missing) - 1}")

        for doc in missing:
            collection.update_one({"_id": doc["_id"]}, {"$set": {"id": next_id}})
            next_id += 1
            total_fixed += 1

    print()
    if total_fixed == 0:
        print("Nothing to fix — every document already has an 'id' field.")
    else:
        print(f"Done. Fixed {total_fixed} document(s) across "
              f"{collections_touched} collection(s).")


if __name__ == "__main__":
    main()