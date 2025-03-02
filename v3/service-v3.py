from flask import Flask, jsonify, request
import string
import redis

app = Flask(__name__)

# Redis configuration
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)

# Base62 characters
BASE62_CHARS = string.digits + string.ascii_letters 

def encode_base62(num):
    """Converts a base-10 number to base-62 string."""
    if num == 0:
        return BASE62_CHARS[0]

    base62 = []
    while num:
        num, remainder = divmod(num, 62)
        base62.append(BASE62_CHARS[remainder])

    return ''.join(reversed(base62))

def get_next_counter():
    """Safely increments the counter using Redis."""
    return redis_client.incr('url_counter')

@app.route("/create", methods=["POST"])
def create_short_url():
    long_url = request.args.get("long_url")
    if not long_url:
        return jsonify({"error": "Missing long_url parameter"}), 400

    # Check if the long URL already exists in Redis
    short_url = redis_client.get(long_url)
    if short_url:
        return jsonify({"short_url": short_url, "long_url": long_url})

    # Generate new short URL
    counter = get_next_counter()
    short_url = encode_base62(counter)
    
    # Store the mapping in Redis
    redis_client.set(short_url, long_url)
    redis_client.set(long_url, short_url)  # Store reverse mapping for quick lookup

    return jsonify({"short_url": short_url, "long_url": long_url})

@app.route("/get", methods=["GET"])
def get_long_url():
    short_url = request.args.get("short_url")
    if not short_url:
        return jsonify({"error": "Missing short_url parameter"}), 400

    # Retrieve the long URL from Redis
    long_url = redis_client.get(short_url)
    if long_url:
        return jsonify({"long_url": long_url})

    return jsonify({"error": "Short URL not found"}), 404

if __name__ == "__main__":
    app.run(debug=True, port=5004)
