import os

import bcrypt
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_socketio import SocketIO, emit, join_room
from functools import wraps
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from config import get_db_connection
from db_setup import setup_db

# Run database setup on startup
setup_db()

secure_cookies = os.getenv("SESSION_COOKIE_SECURE", "False").lower() in ("1", "true", "yes", "on")

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")
app.secret_key = os.getenv("SECRET_KEY", "mentorconnect_secret_key")
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=secure_cookies,
)

auth_serializer = URLSafeTimedSerializer(app.secret_key)
app.permanent_session_lifetime = 7 * 24 * 60 * 60  # 7 days


def generate_auth_token(user):
    return auth_serializer.dumps(
        {
            "user_id": user["id"],
            "email": user["email"],
            "role": user["role"],
        },
        salt="auth-token",
    )


def verify_auth_token(token):
    try:
        return auth_serializer.loads(token, salt="auth-token", max_age=7 * 24 * 60 * 60)
    except (SignatureExpired, BadSignature):
        return None


@app.before_request
def restore_session_from_cookie():
    if "user_id" not in session:
        auth_token = request.cookies.get("auth_token")
        if not auth_token:
            return

        payload = verify_auth_token(auth_token)
        if not payload:
            return

        session["user_id"] = payload["user_id"]
        session["email"] = payload["email"]
        session["role"] = payload["role"]
        session.permanent = True

        conn = get_db_connection()
        if conn is None:
            return

        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT fullname FROM users WHERE id=%s",
            (payload["user_id"],),
        )
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            session["fullname"] = user["fullname"]


def create_notification(user_id, notif_type, message):
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            INSERT INTO notifications (user_id, type, message)
            VALUES (%s, %s, %s)
        """, (user_id, notif_type, message))
        conn.commit()
        
        cursor.execute("SELECT * FROM notifications WHERE id = LAST_INSERT_ID()")
        notif = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if notif:
            notif['created_at'] = notif['created_at'].strftime("%Y-%m-%d %H:%M:%S")
            socketio.emit('new_notification', notif, to=f"user_{user_id}")

# ===============================
# LOGIN REQUIRED DECORATOR
# ===============================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login first.")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


# ===============================
# HOME
# ===============================

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/debug-db")
def debug_db():
    from config import DB_CONFIG
    import mysql.connector
    
    masked_config = DB_CONFIG.copy()
    if "password" in masked_config:
        masked_config["password"] = "***" if masked_config["password"] else ""
        
    info = {
        "DB_CONFIG": masked_config,
        "ENV_VARS": {k: ("***" if "PASS" in k.upper() or "SECRET" in k.upper() else v) for k, v in os.environ.items() if "MYSQL" in k or "DB" in k or k == "DATABASE_URL" or k == "SECRET_KEY"},
        "connection_status": "Not attempted"
    }
    
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        if conn.is_connected():
            info["connection_status"] = "Success"
            cursor = conn.cursor()
            cursor.execute("SHOW TABLES")
            info["tables"] = [r[0] for r in cursor.fetchall()]
            cursor.close()
            conn.close()
        else:
            info["connection_status"] = "Failed (is_connected returned False)"
    except Exception as e:
        import traceback
        info["connection_status"] = f"Failed with exception: {e}"
        info["traceback"] = traceback.format_exc()
        
    return info


# ===============================
# REGISTER
# ===============================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        fullname = request.form["fullname"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        role = request.form["role"]

        if password != confirm_password:
            flash("Passwords do not match.")
            return redirect(url_for("register"))

        conn = get_db_connection()

        if conn is None:
            flash("Database connection failed.")
            return redirect(url_for("register"))

        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT id FROM users WHERE email=%s",
            (email,)
        )

        existing = cursor.fetchone()

        if existing:
            cursor.close()
            conn.close()
            flash("Email already registered.")
            return redirect(url_for("register"))

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        cursor.execute(
            """
            INSERT INTO users
            (fullname,email,password,role)
            VALUES(%s,%s,%s,%s)
            """,
            (
                fullname,
                email,
                hashed_password,
                role
            )
        )

        conn.commit()

        cursor.close()
        conn.close()

        flash("Registration Successful.")
        return redirect(url_for("login"))

    return render_template("register.html")


# ===============================
# LOGIN
# ===============================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"].strip().lower()
        password = request.form["password"]

        conn = get_db_connection()

        if conn is None:
            flash("Database connection failed.")
            return redirect(url_for("login"))

        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM users WHERE email=%s",
            (email,)
        )

        user = cursor.fetchone()
        valid_login = False

        if user:
            stored_password = user.get("password", "")
            if isinstance(stored_password, bytes):
                stored_password = stored_password.decode("utf-8", errors="ignore")

            if stored_password.startswith(("$2b$", "$2y$", "$2a$")):
                try:
                    valid_login = bcrypt.checkpw(
                        password.encode("utf-8"),
                        stored_password.encode("utf-8"),
                    )
                except ValueError:
                    valid_login = False

            if not valid_login and stored_password == password:
                valid_login = True
                new_hashed = bcrypt.hashpw(
                    password.encode("utf-8"),
                    bcrypt.gensalt(),
                ).decode("utf-8")
                cursor.execute(
                    "UPDATE users SET password=%s WHERE id=%s",
                    (new_hashed, user["id"]),
                )
                conn.commit()

        cursor.close()
        conn.close()

        if not user or not valid_login:
            flash("Invalid Email or Password.")
            return redirect(url_for("login"))

        session["user_id"] = user["id"]
        session["fullname"] = user["fullname"]
        session["role"] = user["role"]
        session["email"] = user["email"]
        session.permanent = True

        auth_token = generate_auth_token(user)
        response = redirect(url_for("dashboard"))
        response.set_cookie(
            "auth_token",
            auth_token,
            httponly=True,
            samesite="Lax",
            secure=secure_cookies,
            max_age=7 * 24 * 60 * 60,
        )

        flash("Login Successful.")
        return response

    return render_template("login.html")


# ===============================
# LOGOUT
# ===============================

@app.route("/logout")
def logout():

    session.clear()
    response = redirect(url_for("login"))
    response.set_cookie("auth_token", "", max_age=0, expires=0, secure=secure_cookies)

    flash("Logged out successfully.")
    return response


# ===============================
# DASHBOARD
# ===============================

@app.route("/api/notifications")
@login_required
def get_notifications():
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM notifications
            WHERE user_id=%s AND is_read=FALSE
            ORDER BY created_at DESC
        """, (session["user_id"],))
        notifs = cursor.fetchall()
        for n in notifs:
            n['created_at'] = n['created_at'].strftime("%Y-%m-%d %H:%M:%S")
        cursor.close()
        conn.close()
        return {"status": "success", "notifications": notifs}
    return {"status": "error", "notifications": []}

@app.route("/api/notifications/read", methods=["POST"])
@login_required
def read_notifications():
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE notifications SET is_read=TRUE WHERE user_id=%s", (session["user_id"],))
        conn.commit()
        cursor.close()
        conn.close()
    return {"status": "success"}

@app.route("/dashboard")
@login_required
def dashboard():
    role = session.get("role")
    assigned_mentees = []

    if role == "mentor":
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT
                    users.id AS mentee_id,
                    users.fullname,
                    users.email,
                    mentee_profiles.department,
                    mentee_profiles.interests,
                    mentee_profiles.year
                FROM mentorship_requests
                JOIN users ON mentorship_requests.mentee_id = users.id
                LEFT JOIN mentee_profiles ON users.id = mentee_profiles.user_id
                WHERE mentorship_requests.mentor_id = %s
                  AND mentorship_requests.status = 'Accepted'
            """, (session.get("user_id"),))
            assigned_mentees = cursor.fetchall()
            cursor.close()
            conn.close()

    return render_template(
        "dashboard.html",
        fullname=session.get("fullname"),
        email=session.get("email"),
        role=role,
        assigned_mentees=assigned_mentees
    )

# ===============================
# PROFILE
# ===============================

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():

    conn = get_db_connection()

    if conn is None:
        flash("Database connection failed.")
        return redirect(url_for("dashboard"))

    cursor = conn.cursor(dictionary=True)

    role = session["role"]
    user_id = session["user_id"]

    if request.method == "POST":

        department = request.form["department"]
        bio = request.form["bio"]

        if role == "mentor":

            skills = request.form["skills"]
            experience = request.form["experience"]

            cursor.execute(
                """
                SELECT id
                FROM mentor_profiles
                WHERE user_id=%s
                """,
                (user_id,)
            )

            profile = cursor.fetchone()

            if profile:

                cursor.execute(
                    """
                    UPDATE mentor_profiles
                    SET department=%s,
                        skills=%s,
                        experience=%s,
                        bio=%s
                    WHERE user_id=%s
                    """,
                    (
                        department,
                        skills,
                        experience,
                        bio,
                        user_id
                    )
                )

            else:

                cursor.execute(
                    """
                    INSERT INTO mentor_profiles
                    (
                        user_id,
                        department,
                        skills,
                        experience,
                        bio
                    )
                    VALUES(%s,%s,%s,%s,%s)
                    """,
                    (
                        user_id,
                        department,
                        skills,
                        experience,
                        bio
                    )
                )

        else:

            interests = request.form["interests"]
            year = request.form["year"]

            cursor.execute(
                """
                SELECT id
                FROM mentee_profiles
                WHERE user_id=%s
                """,
                (user_id,)
            )

            profile = cursor.fetchone()

            if profile:

                cursor.execute(
                    """
                    UPDATE mentee_profiles
                    SET department=%s,
                        interests=%s,
                        year=%s,
                        bio=%s
                    WHERE user_id=%s
                    """,
                    (
                        department,
                        interests,
                        year,
                        bio,
                        user_id
                    )
                )

            else:

                cursor.execute(
                    """
                    INSERT INTO mentee_profiles
                    (
                        user_id,
                        department,
                        interests,
                        year,
                        bio
                    )
                    VALUES(%s,%s,%s,%s,%s)
                    """,
                    (
                        user_id,
                        department,
                        interests,
                        year,
                        bio
                    )
                )

        conn.commit()

        flash("Profile saved successfully.")

        cursor.close()
        conn.close()

        return redirect(url_for("dashboard"))

    # --------------------------
    # GET PROFILE
    # --------------------------

    profile = None

    if role == "mentor":

        cursor.execute(
            """
            SELECT *
            FROM mentor_profiles
            WHERE user_id=%s
            """,
            (user_id,)
        )

        profile = cursor.fetchone()

    else:

        cursor.execute(
            """
            SELECT *
            FROM mentee_profiles
            WHERE user_id=%s
            """,
            (user_id,)
        )

        profile = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template(
        "profile.html",
        role=role,
        profile=profile
    )
# ===============================
# MENTORS
# ===============================

@app.route("/mentors")
@login_required
def mentors():

    conn = get_db_connection()

    if conn is None:
        flash("Database connection failed.")
        return redirect(url_for("dashboard"))

    cursor = conn.cursor(dictionary=True)

    search = request.args.get("search", "").strip()
    role = session.get("role")
    mentee_id = session.get("user_id")

    if role == "mentee":
        if search:
            cursor.execute("""
                SELECT
                    users.id AS user_id,
                    users.fullname,
                    users.email,
                    mentor_profiles.department,
                    mentor_profiles.skills,
                    mentor_profiles.experience,
                    mentor_profiles.bio
                FROM users
                LEFT JOIN mentor_profiles
                    ON users.id = mentor_profiles.user_id
                WHERE users.role='mentor'
                  AND users.id NOT IN (
                      SELECT mentor_id
                      FROM mentorship_requests
                      WHERE mentee_id=%s
                        AND status='Accepted'
                  )
                  AND (
                      users.fullname LIKE %s
                      OR mentor_profiles.department LIKE %s
                      OR mentor_profiles.skills LIKE %s
                  )
            """,
            (
                mentee_id,
                f"%{search}%",
                f"%{search}%",
                f"%{search}%"
            ))
        else:
            cursor.execute("""
                SELECT
                    users.id AS user_id,
                    users.fullname,
                    users.email,
                    mentor_profiles.department,
                    mentor_profiles.skills,
                    mentor_profiles.experience,
                    mentor_profiles.bio
                FROM users
                LEFT JOIN mentor_profiles
                    ON users.id = mentor_profiles.user_id
                WHERE users.role='mentor'
                  AND users.id NOT IN (
                      SELECT mentor_id
                      FROM mentorship_requests
                      WHERE mentee_id=%s
                        AND status='Accepted'
                  )
            """,
            (mentee_id,))
    else:
        if search:
            cursor.execute("""
                SELECT
                    users.id AS user_id,
                    users.fullname,
                    users.email,
                    mentor_profiles.department,
                    mentor_profiles.skills,
                    mentor_profiles.experience,
                    mentor_profiles.bio
                FROM users
                LEFT JOIN mentor_profiles
                    ON users.id = mentor_profiles.user_id
                WHERE users.role='mentor'
                  AND (
                      users.fullname LIKE %s
                      OR mentor_profiles.department LIKE %s
                      OR mentor_profiles.skills LIKE %s
                  )
            """,
            (
                f"%{search}%",
                f"%{search}%",
                f"%{search}%"
            ))
        else:
            cursor.execute("""
                SELECT
                    users.id AS user_id,
                    users.fullname,
                    users.email,
                    mentor_profiles.department,
                    mentor_profiles.skills,
                    mentor_profiles.experience,
                    mentor_profiles.bio
                FROM users
                LEFT JOIN mentor_profiles
                    ON users.id = mentor_profiles.user_id
                WHERE users.role='mentor'
            """)

    mentors = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "mentors.html",
        mentors=mentors,
        search=search,
        role=role
    )


# ===============================
# MENTOR PROFILE
# ===============================

@app.route("/mentor/<int:mentor_id>")
@login_required
def mentor_profile(mentor_id):

    conn = get_db_connection()
    if conn is None:
        flash("Database connection failed.")
        return redirect(url_for("mentors"))

    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT
            users.id AS user_id,
            users.fullname,
            users.email,
            mentor_profiles.department,
            mentor_profiles.skills,
            mentor_profiles.experience,
            mentor_profiles.bio
        FROM users
        LEFT JOIN mentor_profiles
            ON users.id=mentor_profiles.user_id
        WHERE users.id=%s
          AND users.role='mentor'
        """,
        (mentor_id,)
    )
    mentor = cursor.fetchone()
    cursor.close()
    conn.close()

    if mentor is None:
        flash("Mentor profile not found.")
        return redirect(url_for("mentors"))

    return render_template(
        "mentor_profile.html",
        mentor=mentor
    )

@app.route("/send_request/<int:mentor_id>")
@login_required
def send_request(mentor_id):

    if session["role"] != "mentee":
        flash("Only mentees can send requests.")
        return redirect(url_for("mentors"))

    mentee_id = session["user_id"]

    conn = get_db_connection()

    if conn is None:
        flash("Database connection failed.")
        return redirect(url_for("mentors"))

    cursor = conn.cursor(dictionary=True)

    # Duplicate request check
    cursor.execute("""
        SELECT *
        FROM mentorship_requests
        WHERE mentor_id=%s
        AND mentee_id=%s
    """,
    (
        mentor_id,
        mentee_id
    ))

    existing = cursor.fetchone()

    if existing:

        flash("Request already sent.")

    else:

        cursor.execute("""
            INSERT INTO mentorship_requests
            (
                mentor_id,
                mentee_id,
                status
            )
            VALUES(%s,%s,%s)
        """,
        (
            mentor_id,
            mentee_id,
            'Pending'
        ))

        conn.commit()

        flash("Mentorship request sent successfully.")
        
        create_notification(
            mentor_id, 
            "request", 
            f"You have a new mentorship request from {session.get('fullname')}."
        )

    cursor.close()
    conn.close()

    return redirect(url_for("mentors"))
# ===============================
# VIEW REQUESTS
# ===============================

@app.route("/requests", endpoint="requests")
@login_required
def requests_page():

    conn = get_db_connection()

    if conn is None:
        flash("Database connection failed.")
        return redirect(url_for("dashboard"))

    cursor = conn.cursor(dictionary=True)

    role = session["role"]
    user_id = session["user_id"]

    # Mentor View
    if role == "mentor":

        cursor.execute("""
            SELECT
                mentorship_requests.id,
                users.fullname,
                COALESCE(mentorship_requests.status, 'Pending') AS status,
                mentorship_requests.request_date AS created_at
            FROM mentorship_requests
            JOIN users
                ON mentorship_requests.mentee_id = users.id
            WHERE mentorship_requests.mentor_id = %s
            ORDER BY mentorship_requests.request_date DESC
        """, (user_id,))

    # Mentee View
    else:

        cursor.execute("""
            SELECT
                mentorship_requests.id,
                users.fullname,
                COALESCE(mentorship_requests.status, 'Pending') AS status,
                mentorship_requests.request_date AS created_at
            FROM mentorship_requests
            JOIN users
                ON mentorship_requests.mentor_id = users.id
            WHERE mentorship_requests.mentee_id = %s
            ORDER BY mentorship_requests.request_date DESC
        """, (user_id,))

    requests = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "requests.html",
        requests=requests,
        role=role
    )


# ===============================
# ACCEPT REQUEST
# ===============================

@app.route("/accept_request/<int:request_id>")
@login_required
def accept_request(request_id):

    if session["role"] != "mentor":
        flash("Access denied.")
        return redirect(url_for("dashboard"))

    conn = get_db_connection()

    if conn is None:
        flash("Database connection failed.")
        return redirect(url_for("requests"))

    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT mentee_id FROM mentorship_requests
        WHERE id=%s AND mentor_id=%s
    """, (request_id, session["user_id"]))
    req = cursor.fetchone()

    if req:
        mentee_id = req["mentee_id"]
        cursor.execute("""
            UPDATE mentorship_requests
            SET status='Accepted'
            WHERE id=%s
        """, (request_id,))
        conn.commit()
        
        create_notification(
            mentee_id,
            "request_accepted",
            f"Your mentorship request was accepted by {session.get('fullname')}."
        )

    cursor.close()
    conn.close()

    flash("Request Accepted Successfully.")

    return redirect(url_for("requests"))


# ===============================
# REJECT REQUEST
# ===============================

@app.route("/reject_request/<int:request_id>")
@login_required
def reject_request(request_id):

    if session["role"] != "mentor":
        flash("Access denied.")
        return redirect(url_for("dashboard"))

    conn = get_db_connection()

    if conn is None:
        flash("Database connection failed.")
        return redirect(url_for("requests"))

    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        UPDATE mentorship_requests
        SET status='Rejected'
        WHERE id=%s
        AND mentor_id=%s
    """,
    (
        request_id,
        session["user_id"]
    ))

    conn.commit()

    cursor.close()
    conn.close()

    flash("Request Rejected Successfully.")

    return redirect(url_for("requests"))
# ===============================
# CHAT LIST
# ===============================

@app.route("/chat")
@login_required
def chat():

    conn = get_db_connection()

    if conn is None:
        flash("Database connection failed.")
        return redirect(url_for("dashboard"))

    cursor = conn.cursor(dictionary=True)

    if session["role"] == "mentor":

        cursor.execute("""
            SELECT DISTINCT
                u.id,
                u.fullname,
                u.role
            FROM users u
            JOIN mentorship_requests mr
                ON mr.mentee_id = u.id
            WHERE mr.mentor_id = %s
              AND mr.status='Accepted'
        """, (session["user_id"],))

    else:

        cursor.execute("""
            SELECT DISTINCT
                u.id,
                u.fullname,
                u.role
            FROM users u
            JOIN mentorship_requests mr
                ON mr.mentor_id = u.id
            WHERE mr.mentee_id = %s
              AND mr.status='Accepted'
        """, (session["user_id"],))

    users = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "chat.html",
        users=users,
        messages=[],
        selected_user=None
    )


# ===============================
# OPEN CHAT
# ===============================

@app.route("/chat/<int:user_id>", methods=["GET", "POST"])
@login_required
def open_chat(user_id):

    conn = get_db_connection()

    if conn is None:
        flash("Database connection failed.")
        return redirect(url_for("chat"))

    cursor = conn.cursor(dictionary=True)

    my_id = session["user_id"]

    # Send Message
    if request.method == "POST":

        message = request.form["message"].strip()

        if message:

            cursor.execute("""
                INSERT INTO chats
                (
                    sender_id,
                    receiver_id,
                    message
                )
                VALUES(%s,%s,%s)
            """,
            (
                my_id,
                user_id,
                message
            ))

            conn.commit()

    # Sidebar Users
    if session["role"] == "mentor":

        cursor.execute("""
            SELECT DISTINCT
                u.id,
                u.fullname
            FROM users u
            JOIN mentorship_requests mr
                ON mr.mentee_id=u.id
            WHERE mr.mentor_id=%s
              AND mr.status='Accepted'
        """, (my_id,))

    else:

        cursor.execute("""
            SELECT DISTINCT
                u.id,
                u.fullname
            FROM users u
            JOIN mentorship_requests mr
                ON mr.mentor_id=u.id
            WHERE mr.mentee_id=%s
              AND mr.status='Accepted'
        """, (my_id,))

    users = cursor.fetchall()

    # Chat History
    cursor.execute("""
        SELECT
            sender_id,
            receiver_id,
            message,
            sent_at
        FROM chats
        WHERE
            (sender_id=%s AND receiver_id=%s)
            OR
            (sender_id=%s AND receiver_id=%s)
        ORDER BY sent_at ASC
    """,
    (
        my_id,
        user_id,
        user_id,
        my_id
    ))

    messages = cursor.fetchall()

    cursor.close()
    conn.close()

    selected_user_data = {
        "id": user_id,
        "fullname": None,
        "role": None,
    }

    if users:
        selected_user_data = next((u for u in users if u["id"] == user_id), selected_user_data)

    return render_template(
        "chat.html",
        users=users,
        messages=messages,
        selected_user=selected_user_data
    )
# ===============================
# SESSIONS
# ===============================

@app.route("/sessions", methods=["GET", "POST"])
@login_required
def sessions():

    conn = get_db_connection()

    if conn is None:
        flash("Database connection failed.")
        return redirect(url_for("dashboard"))

    cursor = conn.cursor(dictionary=True)

    user_id = session["user_id"]
    role = session["role"]

    # ---------------------------
    # CREATE SESSION (Mentor)
    # ---------------------------
    if request.method == "POST":

        if role != "mentor":
            flash("Only mentors can schedule sessions.")
            cursor.close()
            conn.close()
            return redirect(url_for("sessions"))

        mentee_id = request.form["mentee_id"]
        session_date = request.form["session_date"]
        session_time = request.form["session_time"]
        meeting_link = request.form["meeting_link"]

        cursor.execute("""
            INSERT INTO sessions
            (
                mentor_id,
                mentee_id,
                session_date,
                session_time,
                meeting_link
            )
            VALUES(%s,%s,%s,%s,%s)
        """,
        (
            user_id,
            mentee_id,
            session_date,
            session_time,
            meeting_link
        ))

        conn.commit()
        session_id = cursor.lastrowid
        
        create_notification(
            mentee_id,
            "session",
            f"{session.get('fullname')} scheduled a new session on {session_date} at {session_time}."
        )

        flash("Session scheduled successfully.")

        cursor.close()
        conn.close()

        return redirect(url_for("sessions") + f"#session-{session_id}")

    # ---------------------------
    # Accepted mentees (Mentor)
    # ---------------------------
    mentees = []

    if role == "mentor":

        cursor.execute("""
            SELECT
                u.id,
                u.fullname
            FROM users u
            JOIN mentorship_requests mr
                ON mr.mentee_id=u.id
            WHERE mr.mentor_id=%s
            AND mr.status='Accepted'
        """, (user_id,))

        mentees = cursor.fetchall()

        cursor.execute("""
            SELECT
                s.*,
                u.fullname AS mentee_name
            FROM sessions s
            JOIN users u
                ON s.mentee_id=u.id
            WHERE s.mentor_id=%s
            ORDER BY s.session_date,
                     s.session_time
        """, (user_id,))

    else:

        cursor.execute("""
            SELECT
                s.*,
                u.fullname AS mentor_name
            FROM sessions s
            JOIN users u
                ON s.mentor_id=u.id
            WHERE s.mentee_id=%s
            ORDER BY s.session_date,
                     s.session_time
        """, (user_id,))

    sessions_data = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "sessions.html",
        role=role,
        mentees=mentees,
        sessions=sessions_data
    )


# ===============================
# UPDATE SESSION STATUS
# ===============================

@app.route("/update_session/<int:session_id>/<status>")
@login_required
def update_session(session_id, status):

    if session["role"] != "mentor":
        flash("Access denied.")
        return redirect(url_for("sessions"))

    allowed = ["Upcoming", "Completed", "Cancelled"]

    if status not in allowed:
        flash("Invalid status.")
        return redirect(url_for("sessions"))

    conn = get_db_connection()

    if conn is None:
        flash("Database connection failed.")
        return redirect(url_for("sessions"))

    cursor = conn.cursor()

    cursor.execute("""
        UPDATE sessions
        SET status=%s
        WHERE id=%s
        AND mentor_id=%s
    """,
    (
        status,
        session_id,
        session["user_id"]
    ))

    conn.commit()

    cursor.close()
    conn.close()

    flash("Session status updated.")

    return redirect(url_for("sessions"))
# ===============================
# FEEDBACK
# ===============================

@app.route("/feedback", methods=["GET", "POST"])
@login_required
def feedback():

    conn = get_db_connection()

    if conn is None:
        flash("Database connection failed.")
        return redirect(url_for("dashboard"))

    cursor = conn.cursor(dictionary=True)

    user_id = session["user_id"]
    role = session["role"]

    # ----------------------------
    # SUBMIT FEEDBACK (MENTEE)
    # ----------------------------
    if request.method == "POST":

        if role != "mentee":
            flash("Only mentees can submit feedback.")
            cursor.close()
            conn.close()
            return redirect(url_for("feedback"))

        session_id = request.form["session_id"]
        mentor_id = request.form["mentor_id"]
        rating = request.form["rating"]
        comments = request.form["comments"]

        # Prevent duplicate feedback
        cursor.execute("""
            SELECT id
            FROM feedback
            WHERE session_id=%s
            AND mentee_id=%s
        """,
        (
            session_id,
            user_id
        ))

        exists = cursor.fetchone()

        if exists:

            flash("Feedback already submitted.")

        else:

            cursor.execute("""
                INSERT INTO feedback
                (
                    session_id,
                    mentor_id,
                    mentee_id,
                    rating,
                    comments
                )
                VALUES(%s,%s,%s,%s,%s)
            """,
            (
                session_id,
                mentor_id,
                user_id,
                rating,
                comments
            ))

            conn.commit()

            flash("Feedback submitted successfully.")

    # ----------------------------
    # Sessions eligible for feedback
    # ----------------------------

    available_sessions = []

    if role == "mentee":

        cursor.execute("""
            SELECT
                s.id,
                s.mentor_id,
                u.fullname AS mentor_name,
                s.session_date
            FROM sessions s
            JOIN users u
                ON s.mentor_id=u.id
            WHERE s.mentee_id=%s
            AND s.status='Completed'
            ORDER BY s.session_date DESC
        """,
        (user_id,))

        available_sessions = cursor.fetchall()

    # ----------------------------
    # Feedback History
    # ----------------------------

    if role == "mentor":

        cursor.execute("""
            SELECT
                f.*,
                u.fullname AS mentee_name
            FROM feedback f
            JOIN users u
                ON f.mentee_id=u.id
            WHERE f.mentor_id=%s
            ORDER BY f.feedback_date DESC
        """,
        (user_id,))

    else:

        cursor.execute("""
            SELECT
                f.*,
                u.fullname AS mentor_name
            FROM feedback f
            JOIN users u
                ON f.mentor_id=u.id
            WHERE f.mentee_id=%s
            ORDER BY f.feedback_date DESC
        """,
        (user_id,))

    feedbacks = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "feedback.html",
        role=role,
        sessions=available_sessions,
        feedbacks=feedbacks
    )


# ===============================
# SOCKET.IO CHAT
# ===============================

@socketio.on('connect')
def handle_connect():
    if "user_id" in session:
        join_room(f"user_{session['user_id']}")


@socketio.on('send_message')
def handle_send_message(data):
    my_id = session.get("user_id")
    if not my_id:
        return
        
    receiver_id = data.get("receiver_id")
    message = data.get("message", "").strip()
    
    if not receiver_id or not message:
        return
        
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            INSERT INTO chats
            (sender_id, receiver_id, message)
            VALUES(%s, %s, %s)
        """, (my_id, receiver_id, message))
        conn.commit()
        
        cursor.execute("SELECT sent_at FROM chats WHERE id = LAST_INSERT_ID()")
        row = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        created_at = ""
        if row and row.get("sent_at"):
            created_at = row["sent_at"].strftime("%Y-%m-%d %H:%M:%S")
            
        payload = {
            "sender_id": my_id,
            "receiver_id": int(receiver_id),
            "message": message,
            "created_at": created_at
        }
        
        # Emit to receiver and sender so both get it live
        emit('receive_message', payload, to=f"user_{receiver_id}")
        emit('receive_message', payload, to=f"user_{my_id}")
        
        create_notification(
            receiver_id,
            "message",
            f"New message from {session.get('fullname')}"
        )


if __name__ == "__main__":
    socketio.run(app, debug=True, host="0.0.0.0", port=5001, allow_unsafe_werkzeug=True)