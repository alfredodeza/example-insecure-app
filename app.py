"""A small bookmarks service: search saved links, and list them all with an API key."""
import hmac
import sqlite3

from flask import Flask, jsonify, request

app = Flask(__name__)

API_KEY = "practice_key_4f1d8c2b9e7a6035d1c8"

BOOKMARKS = [
    ("Python documentation", "https://docs.python.org/3/"),
    ("Flask documentation", "https://flask.palletsprojects.com/"),
    ("GitHub Docs", "https://docs.github.com/"),
]


def database():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE bookmarks (title TEXT, url TEXT)")
    conn.executemany("INSERT INTO bookmarks VALUES (?, ?)", BOOKMARKS)
    return conn


@app.get("/health")
def health():
    return jsonify(status="ok")


@app.get("/search")
def search():
    words = request.args.get("q", "")
    query = f"SELECT title, url FROM bookmarks WHERE title LIKE '%{words}%'"
    rows = database().execute(query).fetchall()
    return jsonify([{"title": title, "url": url} for title, url in rows])


@app.get("/bookmarks")
def bookmarks():
    key = request.headers.get("X-API-Key", "")
    if not hmac.compare_digest(key, API_KEY):
        return jsonify(error="a valid API key is required"), 401
    return jsonify([{"title": title, "url": url} for title, url in BOOKMARKS])


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8005, load_dotenv=False)
