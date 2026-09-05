from flask import Flask, render_template, request, jsonify
import sqlite3
import os
import cv2

app = Flask(__name__)

DATABASE = "emergency.db"


def init_db():
    conn = sqlite3.connect(DATABASE)

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS emergency_contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/add_contact", methods=["POST"])
def add_contact():

    data = request.get_json()

    name = data.get("name")
    phone = data.get("phone")

    if not name or not phone:
        return jsonify({
            "success": False,
            "message": "Name and phone are required"
        })

    conn = sqlite3.connect(DATABASE)

    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO emergency_contacts (name, phone) VALUES (?, ?)",
        (name, phone)
    )

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": "Contact saved successfully"
    })


@app.route("/contacts")
def get_contacts():

    conn = sqlite3.connect(DATABASE)

    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, name, phone FROM emergency_contacts"
    )

    contacts = cursor.fetchall()

    conn.close()

    return jsonify(contacts)

import os
from flask import request, jsonify

EVIDENCE_FOLDER = "evidence"

os.makedirs(EVIDENCE_FOLDER, exist_ok=True)


@app.route("/save_evidence", methods=["POST"])
@app.route("/analyze_evidence", methods=["POST"])
def analyze_evidence():

    evidence_folder = "evidence"

    if not os.path.exists(evidence_folder):
        return jsonify({
            "success": False,
            "message": "Evidence folder not found."
        })

    files = [
        f for f in os.listdir(evidence_folder)
        if f.lower().endswith(".webm")
    ]

    if not files:
        return jsonify({
            "success": False,
            "message": "No saved evidence found."
        })

    latest_file = max(
        files,
        key=lambda f: os.path.getmtime(
            os.path.join(evidence_folder, f)
        )
    )

    video_path = os.path.join(
        evidence_folder,
        latest_file
    )

    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        return jsonify({
            "success": False,
            "message": "Unable to open evidence video."
        })

    frame_count = 0

    while True:
        ret, frame = cap.read()

        if not ret:
            break

        frame_count += 1

    cap.release()

    return jsonify({
        "success": True,
        "filename": latest_file,
        "frames": frame_count,
        "message": "AI analysis completed successfully."
    })
def save_evidence():

    if "video" not in request.files:
        return jsonify({
            "success": False,
            "message": "No evidence file received"
        })

    video = request.files["video"]

    filename = video.filename

    if not filename:
        filename = "emergency_evidence.webm"

    filepath = os.path.join(
        EVIDENCE_FOLDER,
        filename
    )

    video.save(filepath)

    return jsonify({
        "success": True,
        "message": "Evidence saved successfully"
    })
if __name__ == "__main__":

    init_db()

    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000
    )