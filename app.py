from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "secretkey123"

DB = "medtracker.db"


def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


# -------------------------
# CREATE DATABASE TABLES
# -------------------------

def init_db():

    conn = get_db()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password_hash TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS medicines(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        medicine_name TEXT,
        dosage TEXT,
        time TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS history(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        medicine_id INTEGER,
        date TEXT,
        status TEXT
    )
    """)

    conn.commit()
    conn.close()


init_db()


# -------------------------
# REGISTER
# -------------------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        hashed = generate_password_hash(password)

        conn = get_db()

        try:
            conn.execute(
                "INSERT INTO users(username,password_hash) VALUES (?,?)",
                (username, hashed)
            )
            conn.commit()

        except:
            return "Username already exists"

        conn.close()

        return redirect("/login")

    return render_template("register.html")


# -------------------------
# LOGIN
# -------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()

        user = conn.execute(
            "SELECT * FROM users WHERE username=?",
            (username,)
        ).fetchone()

        conn.close()

        if user and check_password_hash(user["password_hash"], password):

            session["user_id"] = user["id"]
            return redirect("/")

        else:
            return "Invalid login"

    return render_template("login.html")


# -------------------------
# LOGOUT
# -------------------------

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# -------------------------
# DASHBOARD
# -------------------------

@app.route("/")
def index():

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()

    medicines = conn.execute(
        "SELECT * FROM medicines WHERE user_id=?",
        (session["user_id"],)
    ).fetchall()

    today_raw = date.today()
    today_db = today_raw.strftime("%Y-%m-%d")
    today_display = today_raw.strftime("%d-%m-%Y")

    result = []

    for med in medicines:

        med_time_obj = datetime.strptime(med["time"], "%H:%M")

        med_time_24 = med["time"]

        med_time_12 = med_time_obj.strftime("%I:%M %p")

        history = conn.execute(
            "SELECT * FROM history WHERE medicine_id=? AND date=?",
            (med["id"], today_db)
        ).fetchone()

        if history:

            status = history["status"]

        else:

            current_time = datetime.now().time()
            med_time_only = med_time_obj.time()

            if current_time > med_time_only:

                status = "Missed"

                conn.execute(
                    "INSERT INTO history(medicine_id,date,status) VALUES (?,?,?)",
                    (med["id"], today_db, "Missed")
                )

                conn.commit()

            else:
                status = "Pending"

        result.append({
            "id": med["id"],
            "name": med["medicine_name"],
            "dosage": med["dosage"],
            "time": med_time_12,
            "status": status
        })

    conn.close()

    return render_template("index.html", meds=result)


# -------------------------
# ADD MEDICINE
# -------------------------

@app.route("/add", methods=["POST"])
def add():

    name = request.form["name"]
    dosage = request.form["dosage"]
    time = request.form["time"]

    conn = get_db()

    conn.execute(
        "INSERT INTO medicines(user_id,medicine_name,dosage,time) VALUES (?,?,?,?)",
        (session["user_id"], name, dosage, time)
    )

    conn.commit()
    conn.close()

    return redirect("/")


# -------------------------
# MARK AS TAKEN
# -------------------------

@app.route("/taken/<int:id>")
def taken(id):

    today_db = date.today().strftime("%Y-%m-%d")

    conn = get_db()

    conn.execute(
        "INSERT OR REPLACE INTO history(medicine_id,date,status) VALUES (?,?,?)",
        (id, today_db, "Taken")
    )

    conn.commit()
    conn.close()

    return redirect("/")


# -------------------------
# EDIT MEDICINE
# -------------------------

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):

    conn = get_db()

    if request.method == "POST":

        name = request.form["name"]
        dosage = request.form["dosage"]
        time = request.form["time"]

        conn.execute(
            "UPDATE medicines SET medicine_name=?, dosage=?, time=? WHERE id=?",
            (name, dosage, time, id)
        )

        conn.commit()
        conn.close()

        return redirect("/")

    med = conn.execute(
        "SELECT * FROM medicines WHERE id=?",
        (id,)
    ).fetchone()

    conn.close()

    return render_template("edit.html", med=med)


# -------------------------
# DELETE
# -------------------------

@app.route("/delete/<int:id>")
def delete(id):

    conn = get_db()

    conn.execute("DELETE FROM medicines WHERE id=?", (id,))
    conn.execute("DELETE FROM history WHERE medicine_id=?", (id,))

    conn.commit()
    conn.close()

    return redirect("/")


# -------------------------
# HISTORY PAGE
# -------------------------

@app.route("/history")
def history():

    conn = get_db()

    rows = conn.execute("""
    SELECT medicines.medicine_name,
           medicines.time,
           history.date,
           history.status
    FROM history
    JOIN medicines ON medicines.id = history.medicine_id
    ORDER BY history.date DESC
    """).fetchall()

    data = []

    for r in rows:

        time_12 = datetime.strptime(r["time"], "%H:%M").strftime("%I:%M %p")

        date_display = datetime.strptime(
            r["date"], "%Y-%m-%d"
        ).strftime("%d-%m-%Y")

        data.append({
            "medicine_name": r["medicine_name"],
            "time": time_12,
            "date": date_display,
            "status": r["status"]
        })

    conn.close()

    return render_template("history.html", data=data)


if __name__ == "__main__":
    app.run(debug=True)