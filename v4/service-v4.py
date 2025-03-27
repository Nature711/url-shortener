# Redis for caching (with expiration) + DB for persistence

import sqlite3
import string
import redis
from flask import Flask, request, jsonify

app = Flask(__name__)
DB_FILE = "v4/url_mapping.db"
BASE62_ALPHABET = string.digits + string.ascii_lowercase + string.ascii_uppercase

# Initialize Redis client
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)


# Redis with LRU policy
# redis_client = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True, 
#                                   maxmemory=100 * 1024 * 1024,  # 100MB limit
#                                   maxmemory_policy='allkeys-lru')  # LRU eviction policy

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

    # Check Redis for the long URL first
    existing_short_url = redis_client.get(long_url)
    if existing_short_url:
        print(f"(URL already exists & Fetched from Redis: long_url={long_url}, short_url={existing_short_url}")
        return jsonify({"short_url": existing_short_url, "long_url": long_url})

    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()

        # Check if long_url already exists in the database
        cursor.execute("SELECT id FROM url_mapping WHERE long_url = ?", (long_url,))
        row = cursor.fetchone()
        if row:
            short_url = encode_base62(row[0])
            print(f"(URL already exists & Fetched from DB: long_url={long_url}, short_url={short_url}")
            return jsonify({"short_url": short_url, "long_url": long_url})

        # Insert new record and get auto-incremented ID
        cursor.execute("INSERT INTO url_mapping (long_url) VALUES (?)", (long_url,))
        conn.commit()
        short_url = encode_base62(cursor.lastrowid)  # Convert ID to Base62

    return jsonify({"short_url": short_url, "long_url": long_url})

@app.route("/get", methods=["GET"])
def get_long_url():
    short_url = request.args.get("short_url")
    if short_url:
        try:
            id_value = decode_base62(short_url)  # Convert Base62 to Base10
        except ValueError:
            return jsonify({"error": "Invalid short URL"}), 400

        # Check Redis cache first
        cached_long_url = redis_client.get(short_url)
        if cached_long_url:
            print(f"Fetched from Redis: short_url={short_url}, long_url={cached_long_url}")
            redis_client.expire(short_url, 30)  # Update TTL
            redis_client.expire(cached_long_url, 30)  # Update TTL for reverse mapping as well
            return jsonify({"long_url": cached_long_url})

        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT long_url FROM url_mapping WHERE id = ?", (id_value,))
            row = cursor.fetchone()

        if row:
            # Cache the long URL in Redis
            redis_client.set(short_url, row[0], ex=30)  # Cache for 1 hour
            redis_client.set(row[0], short_url, ex=30)  # Cache the reverse mapping for 1 hour as well
            print(f"Fetched from DB: short_url={short_url}, long_url={row[0]}")
            return jsonify({"long_url": row[0]})

    return jsonify({"error": "Short URL not found"}), 404

if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5005)