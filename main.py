# main.py
from flask import Flask, request, redirect, session, jsonify
import sqlite3
import secrets
from datetime import datetime
from linkedin_api import build_auth_url, exchange_code_for_token, post_text_to_linkedin_as_user
import requests
from config import (
    SECRET_KEY,
    DATABASE_PATH,
)


app = Flask(__name__)
app.secret_key = SECRET_KEY


def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """CREATE TABLE IF NOT EXISTS user_tokens (
            user_id TEXT PRIMARY KEY,
            access_token TEXT NOT NULL,
            expires_at TEXT NOT NULL
        )"""
    )
    return conn

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        session["user_id"] = request.form["user_id"]
        return redirect("/dashboard")
    return """
    <form method="post">
      <label>User ID</label>
      <input name="user_id" required />
      <button type="submit">Sign in</button>
    </form>
    """


@app.route("/dashboard")
def dashboard():
    user_id = session.get("user_id")
    if not user_id:
        return redirect("/")
    conn = get_db()
    row = conn.execute(
        "SELECT access_token, expires_at FROM user_tokens WHERE user_id = ?", (user_id,)
    ).fetchone()
    connected = False
    if row:
        expires_at = datetime.fromisoformat(row["expires_at"])
        connected = expires_at > datetime.utcnow()
    button = (
        "<p>Status: Connected</p><form action='/post' method='post'>"
        "<textarea name='text' placeholder='Post text' required></textarea>"
        "<button type='submit'>Post to LinkedIn</button></form>"
        if connected
        else "<p>Status: Not connected</p><a href='/connect'>Connect</a>"
    )
    return f"<p>Hi, {user_id}</p>{button}"


@app.route("/connect")
def connect():
    user_id = session.get("user_id")
    if not user_id:
        return redirect("/")
    state = secrets.token_urlsafe(16)
    session["oauth_state"] = state
    return redirect(build_auth_url(state))


@app.route("/callback")
def callback():
    user_id = session.get("user_id")
    state = session.get("oauth_state")
    if not user_id or not state:
        return redirect("/")
    if request.args.get("state") != state:
        return "Invalid state", 400
    code = request.args.get("code")
    if not code:
        return "Missing code", 400
    access_token, expires_at = exchange_code_for_token(code)
    conn = get_db()
    conn.execute(
        "REPLACE INTO user_tokens (user_id, access_token, expires_at) VALUES (?, ?, ?)",
        (user_id, access_token, expires_at.isoformat()),
    )
    conn.commit()
    return redirect("/dashboard")


@app.route("/post", methods=["POST"])
def post():
    user_id = session.get("user_id")
    if not user_id:
        return redirect("/")
    conn = get_db()
    row = conn.execute(
        "SELECT access_token, expires_at FROM user_tokens WHERE user_id = ?", (user_id,)
    ).fetchone()
    if not row:
        return redirect("/dashboard")
    expires_at = datetime.fromisoformat(row["expires_at"])
    if expires_at <= datetime.utcnow():
        return "Access token expired. Reconnect.", 401
    ok, msg = post_text_to_linkedin_as_user(request.form["text"], row["access_token"])
    if ok:
        return redirect("/dashboard")
    return f"Failed: {msg}", 400


if __name__ == "__main__":
    app.run(debug=True)
