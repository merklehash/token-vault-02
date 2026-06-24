import sqlite3
import os
import uuid
from datetime import datetime

DB = "vault.db"


def get_conn():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tokens (
                id         TEXT PRIMARY KEY,
                name       TEXT NOT NULL,
                token      TEXT NOT NULL,
                status     TEXT DEFAULT 'active',
                billing    REAL DEFAULT 0.0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def create_token():
    print("\n--- Add New Token ---")
    name = input("Service name: ").strip()
    if not name:
        print("Service name cannot be empty.")
        return

    token = input("Token value: ").strip()
    if not token:
        print("Token cannot be empty.")
        return

    billing = input("Billing amount (default 0.0): ").strip()
    try:
        billing = float(billing) if billing else 0.0
    except ValueError:
        billing = 0.0

    token_id = str(uuid.uuid4())[:8]
    n = now()

    with get_conn() as conn:
        conn.execute(
            "INSERT INTO tokens (id, name, token, status, billing, created_at, updated_at) VALUES (?,?,?,?,?,?,?)",
            (token_id, name, token, "active", billing, n, n)
        )

    print(f"Token '{name}' added with ID: {token_id}")


def read_tokens():
    print("\n--- Token List ---")

    query = input("Search by service name (Enter to show all): ").strip()
    status_filter = input("Filter by status (active/inactive, Enter to skip): ").strip().lower()

    sql = "SELECT * FROM tokens WHERE 1=1"
    params = []

    if query:
        sql += " AND name LIKE ?"
        params.append(f"%{query}%")

    if status_filter in ("active", "inactive"):
        sql += " AND status = ?"
        params.append(status_filter)

    sql += " ORDER BY created_at DESC"

    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()

    if not rows:
        print("No tokens found.")
        return

    total_billing = sum(r["billing"] for r in rows)

    print(f"\n{'ID':<10} {'Service':<20} {'Status':<10} {'Billing':>10} {'Created':<18}")
    print("-" * 72)
    for r in rows:
        print(f"{r['id']:<10} {r['name']:<20} {r['status']:<10} ${r['billing']:>9.2f} {r['created_at']:<18}")
    print("-" * 72)
    print(f"{'Total billing:':<42} ${total_billing:>9.2f}")
    print(f"Found: {len(rows)} token(s)")


def update_token():
    print("\n--- Update Token ---")
    token_id = input("Enter token ID: ").strip()

    with get_conn() as conn:
        row = conn.execute("SELECT * FROM tokens WHERE id=?", (token_id,)).fetchone()

        if not row:
            print("Token not found.")
            return

        print(f"Editing: {row['name']} | Status: {row['status']} | Billing: ${row['billing']:.2f}")
        print("Leave field empty to keep current value.")

        new_name = input(f"New service name [{row['name']}]: ").strip()
        new_token = input("New token value [hidden]: ").strip()
        new_status = input(f"New status (active/inactive) [{row['status']}]: ").strip().lower()
        new_billing = input(f"New billing amount [{row['billing']}]: ").strip()

        name = new_name if new_name else row["name"]
        token = new_token if new_token else row["token"]
        status = new_status if new_status in ("active", "inactive") else row["status"]

        try:
            billing = float(new_billing) if new_billing else row["billing"]
        except ValueError:
            billing = row["billing"]
            print("Invalid amount. Keeping current.")

        conn.execute(
            "UPDATE tokens SET name=?, token=?, status=?, billing=?, updated_at=? WHERE id=?",
            (name, token, status, billing, now(), token_id)
        )

    print("Token updated.")


def delete_token():
    print("\n--- Delete Token ---")
    token_id = input("Enter token ID: ").strip()

    with get_conn() as conn:
        row = conn.execute("SELECT name FROM tokens WHERE id=?", (token_id,)).fetchone()

        if not row:
            print("Token not found.")
            return

        confirm = input(f"Delete '{row['name']}' (ID: {token_id})? (yes/no): ").strip().lower()
        if confirm == "yes":
            conn.execute("DELETE FROM tokens WHERE id=?", (token_id,))
            print("Token deleted.")
        else:
            print("Cancelled.")


def show_stats():
    print("\n--- Statistics ---")

    with get_conn() as conn:
        total = conn.execute("SELECT COUNT(*) FROM tokens").fetchone()[0]
        active = conn.execute("SELECT COUNT(*) FROM tokens WHERE status='active'").fetchone()[0]
        inactive = conn.execute("SELECT COUNT(*) FROM tokens WHERE status='inactive'").fetchone()[0]
        total_billing = conn.execute("SELECT SUM(billing) FROM tokens").fetchone()[0] or 0.0
        active_billing = conn.execute("SELECT SUM(billing) FROM tokens WHERE status='active'").fetchone()[0] or 0.0
        top = conn.execute("SELECT name, billing FROM tokens ORDER BY billing DESC LIMIT 1").fetchone()

    if total == 0:
        print("No tokens found.")
        return

    print(f"Total tokens:    {total}")
    print(f"Active:          {active}")
    print(f"Inactive:        {inactive}")
    print(f"Total billing:   ${total_billing:.2f}")
    print(f"Active billing:  ${active_billing:.2f}")
    if top:
        print(f"Highest billing: {top['name']} (${top['billing']:.2f})")


MENU = """
=== Token Vault 02 ===
1. Add token
2. List / Search tokens
3. Update token
4. Delete token
5. Statistics
0. Exit
"""


def main():
    init_db()
    while True:
        print(MENU)
        choice = input("Choice: ").strip()
        if choice == "1":
            create_token()
        elif choice == "2":
            read_tokens()
        elif choice == "3":
            update_token()
        elif choice == "4":
            delete_token()
        elif choice == "5":
            show_stats()
        elif choice == "0":
            print("Bye.")
            break
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()
