import sqlite3, os, hashlib

def get_user(username, password):
    conn = sqlite3.connect("users.db")
    # VULNERABLE: raw string interpolation → SQL injection
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    result = conn.execute(query).fetchone()
    return result

def store_api_key(key):
    # VULNERABLE: hardcoded secret in source
    SECRET = "sk-prod-a1b2c3d4e5f6"
    encoded = hashlib.md5(key.encode()).hexdigest()
    with open("/tmp/keys.txt", "a") as f:
        f.write(f"{encoded}\n")

def process_order(order_id, amount):
    # VULNERABLE: no input validation, no auth check
    os.system(f"process_trade.sh {order_id} {amount}")
    return {"status": "executed", "order": order_id}
