from flask import Flask, render_template, request, jsonify
import sqlite3
import os
import cv2

app = Flask(__name__)

# =====================================================
# CONFIGURATION
# =====================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATABASE = os.path.join(BASE_DIR, "emergency.db")
EVIDENCE_FOLDER = os.path.join(BASE_DIR, "evidence")

os.makedirs(EVIDENCE_FOLDER, exist_ok=True)


# =====================================================
# DATABASE
# =====================================================

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


# Initialize database when app starts
init_db()


# =====================================================
# HOME PAGE
# =====================================================

@app.route("/")
def home():
    return render_template("index.html")


# =====================================================
# ADD EMERGENCY CONTACT
# =====================================================

@app.route("/add_contact", methods=["POST"])
def add_contact():

    try:
        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "message": "Invalid data"
            }), 400

        name = str(data.get("name", "")).strip()
        phone = str(data.get("phone", "")).strip()

        if not name or not phone:
            return jsonify({
                "success": False,
                "message": "Name and phone are required"
            }), 400

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO emergency_contacts (name, phone)
            VALUES (?, ?)
            """,
            (name, phone)
        )

        conn.commit()
        conn.close()

        return jsonify({
            "success": True,
            "message": "Contact saved successfully"
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# =====================================================
# GET EMERGENCY CONTACTS
# =====================================================

@app.route("/contacts", methods=["GET"])
def get_contacts():

    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, name, phone FROM emergency_contacts"
        )

        contacts = cursor.fetchall()

        conn.close()

        return jsonify(contacts)

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# =====================================================
# SAVE EVIDENCE
# =====================================================

@app.route("/save_evidence", methods=["POST"])
def save_evidence():

    try:

        if "video" not in request.files:
            return jsonify({
                "success": False,
                "message": "No evidence file received"
            }), 400

        video = request.files["video"]

        if not video or not video.filename:
            return jsonify({
                "success": False,
                "message": "Invalid evidence file"
            }), 400

        # Generate safe filename
        filename = os.path.basename(video.filename)

        # If filename has no extension
        if not filename.lower().endswith(".webm"):
            filename += ".webm"

        filepath = os.path.join(
            EVIDENCE_FOLDER,
            filename
        )

        video.save(filepath)

        return jsonify({
            "success": True,
            "filename": filename,
            "message": "Evidence saved successfully"
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# =====================================================
# AI ANALYSIS
# =====================================================

@app.route("/analyze_evidence", methods=["POST"])
def analyze_evidence():

    try:

        if not os.path.exists(EVIDENCE_FOLDER):
            return jsonify({
                "success": False,
                "message": "Evidence folder not found."
            }), 404

        # Find saved WEBM evidence files
        files = [
            f for f in os.listdir(EVIDENCE_FOLDER)
            if f.lower().endswith(".webm")
        ]

        if not files:
            return jsonify({
                "success": False,
                "message": "No saved evidence found."
            }), 404

        # Get latest evidence
        latest_file = max(
            files,
            key=lambda f: os.path.getmtime(
                os.path.join(EVIDENCE_FOLDER, f)
            )
        )

        video_path = os.path.join(
            EVIDENCE_FOLDER,
            latest_file
        )

        # Open video using OpenCV
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            return jsonify({
                "success": False,
                "message": "Unable to open evidence video."
            }), 500

        frame_count = 0

        while True:

            ret, frame = cap.read()

            if not ret:
                break

            frame_count += 1

        cap.release()

        # Basic evidence analysis
        if frame_count > 0:

            analysis_message = (
                "AI analysis completed. "
                "Evidence video is readable and "
                "frames were successfully detected."
            )

        else:

            analysis_message = (
                "Evidence video was opened, "
                "but no frames were detected."
            )

        return jsonify({
            "success": True,
            "filename": latest_file,
            "frames": frame_count,
            "message": analysis_message
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "message": "AI analysis failed: " + str(e)
        }), 500


# =====================================================
# RUN APPLICATION
# =====================================================

if __name__ == "__main__":

    app.run(
        debug=True,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )