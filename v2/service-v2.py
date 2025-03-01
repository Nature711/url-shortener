import sqlite3
import string

from flask import Flask, request, jsonify

app = Flask(__name__)
DB_FILE = "v2/url_mapping.db"
BASE62_ALPHABET = string.digits + string.ascii_lowercase + string.ascii_uppercase


def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS url_mapping (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            long_url TEXT UNIQUE NOT NULL
        )
        """)
        conn.commit()


def encode_base62(num):
    """Convert Base10 integer to Base62 string."""
    if num == 0:
        return BASE62_ALPHABET[0]
    
    base62 = []
    while num:
        num, remainder = divmod(num, 62)
        base62.append(BASE62_ALPHABET[remainder])

    return ''.join(reversed(base62))


def decode_base62(base62_str):
    """Convert Base62 string back to Base10 integer."""
    num = 0
    for char in base62_str:
        num = num * 62 + BASE62_ALPHABET.index(char)
    
    return num


@app.route("/create", methods=["POST"])
def create_short_url():
    long_url = request.args.get("long_url")
    if not long_url:
        return jsonify({"error": "long_url is required"}), 400

    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()

        # Check if long_url already exists
        cursor.execute("SELECT id FROM url_mapping WHERE long_url = ?", (long_url,))
        row = cursor.fetchone()
        if row:
            short_url = encode_base62(row[0])
            return jsonify({"short_url": short_url, "long_url": long_url})

        # Insert new record and get auto-incremented ID
        cursor.execute("INSERT INTO url_mapping (long_url) VALUES (?)", (long_url,))
        conn.commit()
        short_url = encode_base62(cursor.lastrowid)  # Convert ID to Base62

    return jsonify({"short_url": short_url})


@app.route("/get", methods=["GET"])
def get_long_url():
    short_url = request.args.get("short_url")
    if short_url: 
        try:
            id_value = decode_base62(short_url)  # Convert Base62 to Base10
        except ValueError:
            return jsonify({"error": "Invalid short URL"}), 400

        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT long_url FROM url_mapping WHERE id = ?", (id_value,))
            row = cursor.fetchone()

        if row:
            return jsonify({"long_url": row[0]})

    return jsonify({"error": "Short URL not found"}), 404


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
