import os
import fcntl
import base64
from flask import Flask, request, jsonify

app = Flask(__name__)

COUNTER_FILE = "v1.1/counter.txt"
MAPPING_FILE = "v1.1/url_mapping.txt"
url_mapping = {}

# Check if MAPPING_FILE exists, if not, create it
if not os.path.exists(MAPPING_FILE):
    with open(MAPPING_FILE, "w") as f:
        # Create an empty mapping file if it doesn't exist
        pass
else:
    with open(MAPPING_FILE, "r") as f:
        for line in f:
            short_url, long_url = line.strip().split(",", 1)
            url_mapping[short_url] = long_url

# Check if COUNTER_FILE exists, if not, create and initialize it
if not os.path.exists(COUNTER_FILE):
    with open(COUNTER_FILE, "w") as f:
        f.write("1")  # Initialize counter to 1
else:
    with open(COUNTER_FILE, "r") as f:
        counter = int(f.read().strip())

def base62_encode(num):
    """Converts a base 10 number to base 62"""
    chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    if num == 0:
        return chars[0]
    
    result = []
    while num:
        num, remainder = divmod(num, 62)
        result.append(chars[remainder])
    
    return "".join(reversed(result))

def get_next_counter():
    """Safely increments the counter using file locking"""
    with open(COUNTER_FILE, "r+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)  # Acquire an exclusive lock
        counter = int(f.read().strip())  # Read current counter
        f.seek(0)  # Move cursor to beginning
        f.write(str(counter + 1))  # Increment and update counter
        f.truncate()  # Ensure no leftover characters
        fcntl.flock(f, fcntl.LOCK_UN)  # Release lock
    return counter

@app.route("/create", methods=["POST"])
def create_short_url():
    long_url = request.args.get("long_url")
    if not long_url:
        return jsonify({"error": "long_url is required"}), 400

    # Check if long URL is already mapped
    with open(MAPPING_FILE, "r") as db:
        for line in db:
            short, existing_long_url = line.strip().split(",", 1)
            if existing_long_url == long_url:
                return jsonify({"short_url": short})

    # Get next counter safely
    counter_value = get_next_counter()
    short_url = base62_encode(counter_value)

    # Store mapping
    with open(MAPPING_FILE, "a") as db:
        db.write(f"{short_url},{long_url}\n")

    return jsonify({"short_url": short_url, "long_url": long_url})

@app.route("/get", methods=["GET"])
def get_long_url():
    short_url = request.args.get("short_url")
    if short_url: 
        with open(MAPPING_FILE, "r") as db:
            for line in db:
                short, long_url = line.strip().split(",", 1)
                if short == short_url:
                    return jsonify({"long_url": long_url})

    return jsonify({"error": "Short URL not found"}), 404

if __name__ == "__main__":
    app.run(debug=True, port=5002)
