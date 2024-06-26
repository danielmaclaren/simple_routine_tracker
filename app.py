import sqlite3
import datetime

from flask import Flask, render_template, request, session, redirect, jsonify
from flask_session import Session
from helpers import login_required, apology
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = "test"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

conn = sqlite3.connect('workout.db',  check_same_thread=False)
db = conn.cursor()

db.execute("""CREATE TABLE IF NOT EXISTS Users (
        UserID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        Username TEXT NOT NULL,
        Hash TEXT NOT NULL)""")

db.execute("""CREATE TABLE IF NOT EXISTS Workouts (
        WorkoutID INTEGER PRIMARY KEY AUTOINCREMENT,
        UserID INT,
        WorkoutDate DATE NOT NULL,
        CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (UserID) REFERENCES Users(UserID))""")

db.execute("""CREATE TABLE IF NOT EXISTS Exercises (
        ExerciseID INTEGER PRIMARY KEY AUTOINCREMENT,
        Name VARCHAR(50),
        CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")

db.execute("""CREATE TABLE IF NOT EXISTS WorkoutExercises (
        WorkoutExercise INTEGER PRIMARY KEY AUTOINCREMENT,
        WorkoutID INT,
        ExerciseID INT,
        Sets INT,
        Weight DECIMAL(5,2),
        Reps INT,
        FOREIGN KEY (WorkoutID) REFERENCES Workouts(WorkoutID),
        FOREIGN KEY (ExerciseID) REFERENCES Exercises(ExerciseID));""")

conn.commit()

exercise_button_clicks = 0

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/")
def index():
    #user_id = session["user_id"]

    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():

    session.clear()

    if request.method == "POST":

        if not request.form.get("username"):
            return apology("must provide username", 400)
        
        elif not request.form.get("password"):
            return apology("must provide password", 400)
        
        rows = db.execute(
            "SELECT * FROM Users WHERE Username = ?", (request.form.get("username"),)
        )
        conn.commit()

        data = rows.fetchall()

        if len(data) != 1 or not check_password_hash(
            data[0][2], request.form.get("password")
        ):
            return apology("Invalid username and/or password", 400)
        
        session["user_id"] = data[0][0]

        return redirect("/")
    
    elif request.method == "GET":
        return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    #session.pop("user_id", None)
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":

        if not request.form.get("username"):
            return apology("must provide username", 400)

        elif not request.form.get("password"):
            return apology("must provide password", 400)

        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords must match", 400)

        rows = db.execute(
            "SELECT * FROM Users WHERE Username = ?", (request.form.get("username"),)
        )

        data = rows.fetchall()
        
        if data:
            return apology(
                "username is already taken, please use another username", 400
            )
        else:
            hash_password = generate_password_hash(request.form.get("password"))

            new_user = db.execute(
                "INSERT INTO Users (Username, Hash) VALUES (?, ?)",
                (request.form.get("username"),
                hash_password,)
            )
            conn.commit()

            new_user_id = new_user.lastrowid


        session["user_id"] = new_user_id

        return redirect("/")

    elif request.method == "GET":
        return render_template("register.html")

@app.route("/aboutme")
@login_required
def aboutme():
    return render_template("aboutme.html")

@app.route("/training")
@login_required
def training():

    if request.method == "POST":

        return redirect("/")

    else:
        workout_date = datetime.datetime.now()
        user_id = session["user_id"]

        db.execute(
            "INSERT INTO Workouts (UserID, WorkoutDate) VALUES (?, ?)", (user_id, workout_date)
            )
        
        workout_id = db.lastrowid
        session["workout_id"] = workout_id

        return render_template("training.html")

@app.route('/addexerciseclick', methods=['POST'])
def addexerciseclick():
    if request.method == "POST":
        data = request.get_json()
        exercisetitle = data.get("exercisetitle")
        if not exercisetitle:
            return jsonify({"message": "Exercise title is required"}), 400

        rows = db.execute(
            "SELECT ExerciseID FROM Exercises WHERE Name = ?", (exercisetitle,)
        )

        data = rows.fetchall()

        if not data:
            db.execute(
                "INSERT INTO Exercises (Name) VALUES (?)", (exercisetitle,)
            )
            conn.commit()
            exercise_id = db.lastrowid
            session["exercise_id"] = exercise_id
            return jsonify({"message": "Exercise was added successfully"}), 201
        else:
            exercise_id = data[0][0]
            session["exercise_id"] = exercise_id
            return jsonify({"message": "Exercise already exists"}), 200


@app.route('/addsetclick', methods=['POST'])
def addsetclick():
    if request.method == "POST":
        data = request.get_json()
        workoutobj = data.get("workoutObj")

        if not workoutobj:
            return jsonify({"message": "Invalid data"}), 400

        workout_id = session.get("workout_id")
        exercise_id = session.get("exercise_id")
        weight = workoutobj.get("weight")
        reps = workoutobj.get("reps")

        db.execute(
            "INSERT INTO WorkoutExercises (WorkoutID, ExerciseID, Weight, Reps) VALUES (?, ?, ?, ?)", (workout_id, exercise_id, weight, reps,)
        )
        conn.commit()
        return jsonify({"message": "Data inserted successfully"}), 201


@app.route("/history")
@login_required
def history():
    return render_template("history.html")

if __name__ == "__main__":
    app.run(debug=True)