from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    redirect,
    session

)
from datetime import datetime, timedelta
import sqlite3
import random
import smtplib
from email.mime.text import MIMEText

try:
    from gpt4all import GPT4All
except:
    GPT4All = None

app = Flask(__name__)
app.secret_key = "hindalco_secret_key"

# =========================
# EMAIL CONFIGURATION
# =========================

EMAIL_ADDRESS = "deviarchanabhoi@gmail.com"
EMAIL_PASSWORD = "tllu raea enlo hkil"

AUTHORIZED_ADMINS = [
    "deviarchanabhoi@gmail.com",
    "saroj.k.pradhan@adityabirla.com"
]

# =========================
# LOAD AI MODEL
# =========================

model = None

try:

    if GPT4All:

        model = GPT4All(
            "mistral-7b-instruct-v0.1.Q4_0.gguf"
        )

except Exception as e:

    print("MODEL ERROR:", e)

    model = None


# =========================
# DATABASE CONNECTION
# =========================

def get_db_connection():

    conn = sqlite3.connect("chatbot.db")
    conn.row_factory = sqlite3.Row

    return conn


# =========================
# CREATE TABLES
# =========================

def create_tables():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        limit_enabled TEXT DEFAULT 'true',
        max_messages INTEGER DEFAULT 50,
        reset_hours INTEGER DEFAULT 1
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admin_emails (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_limits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        message_count INTEGER DEFAULT 0
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS custom_queries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        keyword TEXT,
        response TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chat_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    employee_id TEXT,
    department TEXT,
    message TEXT,
    reply TEXT,
    created_at TEXT
)
    """)

    conn.commit()

    cursor.execute("SELECT * FROM settings")
    settings = cursor.fetchone()

    if settings is None:

        cursor.execute("""
        INSERT INTO settings
        (
            limit_enabled,
            max_messages,
            reset_hours
        )
        VALUES
        (
            'true',
            50,
            1
        )
        """)

        conn.commit()

    cursor.execute("SELECT * FROM admin_emails")
    admin = cursor.fetchone()

    if admin is None:

        cursor.execute(
            "INSERT INTO admin_emails (email) VALUES (?)",
            ("deviarchanabhoi@gmail.com",)
        )

        conn.commit()

    conn.close()


create_tables()


# =========================
# CHAT LIMIT FUNCTION
# =========================

def check_user_limit(username):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM settings ORDER BY id DESC LIMIT 1"
    )

    settings = cursor.fetchone()

    if settings is None:

        conn.close()

        return True

    limit_enabled = str(
        settings["limit_enabled"]
    ).lower()

    max_messages = int(
        settings["max_messages"]
    )

    if limit_enabled == "false":

        conn.close()

        return True

    cursor.execute(
        "SELECT * FROM user_limits WHERE username=?",
        (username,)
    )

    user = cursor.fetchone()

    if user is None:

        cursor.execute(
            """
            INSERT INTO user_limits
            (
                username,
                message_count
            )
            VALUES (?, ?)
            """,
            (
                username,
                1
            )
        )

        conn.commit()
        conn.close()

        return True

    current_count = int(user["message_count"])

    if current_count >= max_messages:

        conn.close()

        return False

    cursor.execute(
        """
        UPDATE user_limits
        SET message_count = ?
        WHERE username = ?
        """,
        (
            current_count + 1,
            username
        )
    )

    conn.commit()
    conn.close()

    return True


# =========================
# WELCOME PAGE
# =========================

@app.route("/")
def welcome():

    return render_template("welcome.html")


# =========================
# LOGIN PAGE
# =========================

@app.route("/login")
def login():

    return render_template("login.html")


# =========================
# LOGIN PROCESS
# =========================

@app.route("/login-user", methods=["POST"])
def login_user():

    username = request.form["username"]
    employee_id = request.form["employee_id"]
    department = request.form["department"]

    session["username"] = username
    session["employee_id"] = employee_id
    session["department"] = department

    return redirect("/dashboard")


# =========================
# DASHBOARD
# =========================

@app.route("/dashboard")
def dashboard():

    if "username" not in session:

        return redirect("/login")

    return render_template(
        "index.html",
        username=session["username"]
    )


# =========================
# ADMIN LOGIN PAGE
# =========================

@app.route("/admin-email-login")
def admin_email_login():

    return render_template(
        "admin_email_login.html"
    )


# =========================
# SEND EMAIL OTP
# =========================

@app.route("/send-email-otp", methods=["POST"])
def send_email_otp():

    email = request.form["email"].strip().lower()

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM admin_emails WHERE email=?",
        (email,)
    )

    admin_data = cursor.fetchone()

    conn.close()

    if not admin_data:

        return "Unauthorized Admin"

    otp = str(
        random.randint(100000, 999999)
    )

    session["email_otp"] = otp
    session["admin_email"] = email

    msg = MIMEText(
        f"Your Hindalco Admin OTP is: {otp}"
    )

    msg["Subject"] = "Hindalco Admin OTP"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = email

    try:

        server = smtplib.SMTP(
            "smtp.gmail.com",
            587
        )

        server.starttls()

        server.login(
            EMAIL_ADDRESS,
            EMAIL_PASSWORD
        )

        server.send_message(msg)

        server.quit()

    except Exception as e:

        return f"Unable to send OTP: {e}"

    return redirect("/verify-email-otp")


# =========================
# VERIFY OTP
# =========================

@app.route("/verify-email-otp", methods=["GET", "POST"])
def verify_email_otp():

    if request.method == "POST":

        entered_otp = request.form["otp"]

        real_otp = session.get("email_otp")

        if entered_otp == real_otp:

            session["admin"] = True

            return redirect("/admin")

        return render_template(
    "invalid_otp.html"
)

    return render_template(
        "verify_email_otp.html"
    )


# =========================
# CHAT
# =========================

@app.route("/chat", methods=["POST"])
def chat():

    if "username" not in session:

        return jsonify({
            "reply": "Please login first."
        })

    user_message = request.json["message"]

    # SAVE QUERY TO SHARED DATABASE

    try:

        import os

        db_path = os.path.abspath("../shared_data.db")
        print("USING DB:", db_path)

        conn2 = sqlite3.connect("../shared_data.db")

        cursor2 = conn2.cursor()

        created_date = datetime.today().strftime("%Y-%m-%d")

        cursor2.execute(
          """
          INSERT INTO queries
          (
               username,
               query
          )
          VALUES (?, ?)
         """,
          (
             session["username"],
             user_message
          )
   )

        conn2.commit()

        # CREATE TASK IN TASK MANAGER

        task_conn = sqlite3.connect(
            r"C:\Users\sunit\OneDrive\Desktop\task_management_app\task.db"
        )
        print("CHATBOT WRITING TO:")
        print(r"C:\Users\sunit\OneDrive\Desktop\task_management_app\task.db")

        task_cursor = task_conn.cursor()

        due_date = (
            datetime.today() +
            timedelta(days=10)
        ).strftime("%Y-%m-%d")

        task_cursor.execute(
            """
            INSERT INTO tasks
            (
                title,
                description,
                due_date,
                priority,
                status,
                assigned_to,
                created_date,
                active
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_message,
                "Generated from Chatbot",
                due_date,
                "Low",
                "Pending",
                session["username"],
                created_date,
                1
            )
        )

        task_conn.commit()

        cursor_check = task_conn.cursor()
        cursor_check.execute("SELECT MAX(id) FROM tasks")
        print("LATEST TASK ID =", cursor_check.fetchone()[0])

        print("TASK CREATED SUCCESSFULLY")

        task_conn.close()

        conn2.close()

    except Exception as e:
       import traceback
       traceback.print_exc()

       print("========== ERROR ==========")
       print(type(e))
       print(e)
       print("========== ERROR ==========")

    message = user_message.lower()

    username = session["username"]

    allowed = check_user_limit(username)

    if not allowed:

        return jsonify({
            "reply": """
🚫 Chat Limit Reached

You have reached your maximum chat limit.

Please wait until admin resets your limit.
"""
        })

# =========================
# PREDEFINED RESPONSES
# =========================

    predefined_responses = {

        "hello,hi,hey,hii,hy,good morning,good evening":
        """
👋 Hello!

Welcome to Hindalco AI Assistant.

I am your 24/7 IT Support Assistant.

How may I help you today?
""",

        "wifi issue,network issue,no internet,no network":
        """
🌐 Network Connection Issue

1. Restart WiFi Router
2. Restart Laptop/Desktop
3. Forget and reconnect WiFi
4. Reconnect LAN cable properly
5. Check airplane mode is OFF

Please contact IT Department if issue continues.
""",

        "laptop slow,system slow,pc slow":
        """
💻 Laptop Performance Issue

1. Press Windows + R
2. Type %temp%
3. Delete temporary files
4. Restart laptop

If issue continues contact IT Department.
""",

        "camera not working,webcam issue,camera issue":
        """
📷 Camera Issue

1. Check camera shutter open or closed
2. Enable camera permissions
3. Restart Teams
4. Restart laptop

If issue continues contact IT Department.
""",

        "teams mic,microphone not working,mic issue":
        """
🎤 Microphone Issue

1. Unmute headset/laptop mic
2. Check Teams microphone permissions
3. Restart MS Teams
4. Restart laptop

If issue continues contact IT Department.
""",

        "mail issue,outlook issue,email not working":
        """
📧 Outlook/Mail Issue

1. Restart Outlook
2. Check internet connection
3. Sync mail again
4. Restart device

If issue continues contact IT Department.
""",

        "new phone mail issue,outlook not working in new phone":
        """
📱 New Phone Mail Setup

1. Install Intune Company Portal
2. Register device
3. Install Outlook
4. Add work account

If issue continues contact IT Department.
""",

        "unable to login,login issue,password issue":
        """
🔐 Login Issue

1. Check username/password
2. Reset password
3. Restart device
4. Try again

If issue continues contact IT Department.
""",

        "c drive full,disk full,storage issue":
        """
💾 Storage Issue

1. Open Disk Cleanup
2. Delete temp files
3. Remove unwanted downloads
4. Use OneDrive for storage

If issue continues contact IT Department.
""",

        "printer issue,printer not working":
        """
🖨 Printer Issue

1. Restart printer
2. Check paper and cable
3. Reconnect printer
4. Restart desktop

If issue continues contact IT Department.
""",

        "vpn issue,vpn not connecting":
        """
🔒 VPN Issue

1. Restart VPN
2. Check internet
3. Login again
4. Restart laptop

If issue continues contact IT Department.
""",

        "poornata site not opening,poornata issue":
        """
🌐 Poornata Site Issue

1. Clear browser history
2. Update browser
3. Restart browser
4. Try again

If issue continues contact IT Department.
""",

        "ekayaan site issue":
        """
🌐 Ekayaan Site Issue

1. Clear browser history
2. Update browser
3. Restart browser
4. Try again

If issue continues contact IT Department.
""",

        "thank you,thanks":
        """
😊 You're Welcome!

Happy to assist you anytime.
""",

        "bye,goodbye":
        """
👋 Thank You for Using Hindalco AI Assistant.

Have a great day ahead!
"""
    }

# =========================
# LOAD ADMIN QUERIES
# =========================

    try:

        conn = get_db_connection()

        custom_queries = conn.execute(
            "SELECT * FROM custom_queries"
        ).fetchall()

        conn.close()

        for row in custom_queries:

            predefined_responses[
                row["keyword"].lower()
            ] = row["response"]

    except Exception as e:

        print("CUSTOM QUERY ERROR:", e)

# =========================
# CHECK PREDEFINED RESPONSES
# =========================

    for keywords, response in predefined_responses.items():

        keyword_list = keywords.split(",")

        for keyword in keyword_list:

            if keyword.strip().lower() == message.strip().lower():

                try:

                    conn = get_db_connection()
                    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    conn.execute(
                        """
                        INSERT INTO chat_logs
                        (
                            username,
                            employee_id,
                            department,
                            message,
                            reply,
                            created_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            session.get("username"),
                            session.get("employee_id"),
                            session.get("department"),
                            user_message,
                            response,
                            current_time
                        )
                    )

                    conn.commit()

                    conn.close()

                except Exception as e:

                    print("LOG ERROR:", e)

                return jsonify({
                    "reply": response
                })   

# =========================
# AI RESPONSE
# =========================

    prompt = f"""
You are Hindalco AI Assistant.

Provide professional IT support answers.

User:
{user_message}

Assistant:
"""

    try:

        if model is not None:

            response = model.generate(
                prompt,
                max_tokens=300,
                temp=0.5
            )

            bot_reply = response.strip()

        else:

            bot_reply = """
⚠️ AI model not loaded.

Please check GPT4All model file.
"""

    except Exception as e:

        print("AI ERROR:", e)

        bot_reply = """
⚠️ AI Server Temporary Issue

Please try supported IT support queries.
"""
    # =========================
    # SAVE CHAT LOGS
    # =========================

    try:

        conn = get_db_connection()
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn.execute(
            """
            INSERT INTO chat_logs
            (
                username,
                employee_id,
                department,
                message,
                reply,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                session.get("username"),
                session.get("employee_id"),
                session.get("department"),
                user_message,
                bot_reply,
                current_time
            )
        )

        conn.commit()
        conn.close()

    except Exception as e:

        print("LOG ERROR:", e)

    return jsonify({
        "reply": bot_reply
    })

# =========================
# ADMIN PANEL
# =========================

@app.route("/admin")
def admin():

    if "admin" not in session:

        return redirect(
            "/admin-email-login"
        )

    conn = get_db_connection()

    settings = conn.execute(
        "SELECT * FROM settings ORDER BY id DESC LIMIT 1"
    ).fetchone()

    custom_queries = conn.execute(
        "SELECT * FROM custom_queries"
    ).fetchall()

    admin_emails = conn.execute(
        "SELECT * FROM admin_emails"
    ).fetchall()

    conn.close()

    return render_template(
        "admin.html",
        settings=settings,
        custom_queries=custom_queries,
        admin_emails=admin_emails
    )


# =========================
# ADD QUERY
# =========================

@app.route("/add-query", methods=["POST"])
def add_query():

    if "admin" not in session:

        return redirect(
            "/admin-email-login"
        )

    keyword = request.form.get(
        "keyword"
    )

    response = request.form.get(
        "response"
    )

    conn = get_db_connection()

    conn.execute(
        """
        INSERT INTO custom_queries
        (
            keyword,
            response
        )
        VALUES (?, ?)
        """,
        (
            keyword,
            response
        )
    )

    conn.commit()
    conn.close()

    return redirect("/admin")
# =========================
# DELETE QUERY
# =========================

@app.route("/delete-query/<int:id>")
def delete_query(id):

    if "admin" not in session:

        return redirect("/admin-email-login")

    conn = get_db_connection()

    conn.execute(
        "DELETE FROM custom_queries WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/admin")    
# =========================
# ADD ADMIN EMAIL
# =========================

@app.route("/add-admin-email", methods=["POST"])
def add_admin_email():

    if "admin" not in session:

        return redirect(
            "/admin-email-login"
        )

    email = request.form.get("email")

    conn = get_db_connection()

    conn.execute(
        """
        INSERT INTO admin_emails
        (
            email
        )
        VALUES (?)
        """,
        (email,)
    )

    conn.commit()
    conn.close()

    return redirect("/admin")
# =========================
# DELETE ADMIN EMAIL
# =========================

@app.route("/delete-admin-email/<int:id>")
def delete_admin_email(id):

    if "admin" not in session:

        return redirect(
            "/admin-email-login"
        )

    conn = get_db_connection()

    conn.execute(
        "DELETE FROM admin_emails WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/admin")

# =========================
# SAVE SETTINGS
# =========================

@app.route("/save-settings", methods=["POST"])
def save_settings():

    if "admin" not in session:

        return redirect(
            "/admin-email-login"
        )

    limit_enabled = request.form.get(
        "limit_enabled"
    )

    max_messages = request.form.get(
        "max_messages"
    )

    reset_hours = request.form.get(
        "reset_hours"
    )

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM settings")

    cursor.execute(
        """
        INSERT INTO settings
        (
            limit_enabled,
            max_messages,
            reset_hours
        )
        VALUES (?, ?, ?)
        """,
        (
            limit_enabled,
            max_messages,
            reset_hours
        )
    )

    conn.commit()
    conn.close()

    return redirect("/admin")


# =========================
# RESET USER LIMITS
# =========================

@app.route("/reset-user-limits")
def reset_user_limits():

    if "admin" not in session:

        return redirect(
            "/admin-email-login"
        )

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM user_limits"
    )

    conn.commit()
    conn.close()

    return redirect("/admin")


# =========================
# LOGS PAGE
# =========================

@app.route("/logs")
def logs():

    if "admin" not in session:

        return redirect(
            "/admin-email-login"
        )

    conn = get_db_connection()

    logs = conn.execute(
        """
        SELECT
            id,
            username,
            employee_id,
            department,
            message,
            reply,
            created_at
        FROM chat_logs
        ORDER BY id DESC
        """
    ).fetchall()

    conn.close()

    return render_template(
        "logs.html",
        logs=logs
    )


# =========================
# LOGOUT
# =========================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


# =========================
# RUN APP
# =========================

if __name__ == "__main__":
    app.run(debug=True, port=5001)
