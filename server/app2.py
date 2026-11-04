import hmac
import os
import secrets
from decimal import Decimal, InvalidOperation
from functools import wraps

import click
import mysql.connector
from dotenv import load_dotenv
from flask import Flask, abort, flash, g, redirect, render_template, request, session, url_for
from mysql.connector import Error
from werkzeug.security import check_password_hash, generate_password_hash

load_dotenv()

app2 = Flask(
    __name__,
    template_folder="../client",
    static_folder="../client/static",
    static_url_path="/static",
)
app2.config.from_mapping(
    SECRET_KEY=os.environ.get("SECRET_KEY") or secrets.token_hex(32),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true",
    MAX_CONTENT_LENGTH=1024 * 1024,
    CSRF_ENABLED=True,
)

db_config = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": int(os.environ.get("DB_PORT", "3306")),
    "user": os.environ.get("DB_USER", "root"),
    "password": os.environ.get("DB_PASSWORD", ""),
    "database": os.environ.get("DB_NAME", "employee_management"),
    "charset": "utf8mb4",
}

ROLE_CONFIG = {
    "employee": {
        "table": "emp_login",
        "id": "emp_id",
        "username": "emp_username",
        "password": "emp_password",
    },
    "admin": {
        "table": "admin_login",
        "id": "admin_id",
        "username": "admin_username",
        "password": "admin_password",
    },
}


def get_db():
    """Create one request-scoped database connection."""
    if "mysql_db" not in g:
        g.mysql_db = mysql.connector.connect(**db_config)
    return g.mysql_db


def execute_db(query, args=(), commit=False):
    """Execute a parameterized query and never hide database failures."""
    conn = get_db()
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, args)
        if commit:
            conn.commit()
        if cursor.with_rows:
            return cursor.fetchall()
        return cursor.rowcount
    except Error:
        if commit and conn.is_connected():
            conn.rollback()
        app2.logger.exception("Database operation failed")
        raise
    finally:
        if cursor is not None:
            cursor.close()


@app2.teardown_appcontext
def close_db(error):
    conn = g.pop("mysql_db", None)
    if conn is not None and conn.is_connected():
        conn.close()


def csrf_token():
    token = session.get("_csrf_token")
    if token is None:
        token = secrets.token_hex(32)
        session["_csrf_token"] = token
    return token


app2.jinja_env.globals["csrf_token"] = csrf_token


@app2.before_request
def protect_against_csrf():
    if request.method != "POST" or not app2.config["CSRF_ENABLED"]:
        return
    expected = session.get("_csrf_token", "")
    supplied = request.form.get("csrf_token", "")
    if not expected or not supplied or not hmac.compare_digest(expected, supplied):
        abort(400, description="The form expired or was invalid. Please try again.")


@app2.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


@app2.context_processor
def inject_user():
    return {
        "is_admin": session.get("role") == "admin",
        "current_username": session.get("username"),
    }


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get("user_id") or session.get("role") not in ROLE_CONFIG:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped_view


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped_view(*args, **kwargs):
        if session.get("role") != "admin":
            abort(403)
        return view(*args, **kwargs)

    return wrapped_view


def parse_positive_int(value, label):
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be a whole number.") from exc
    if parsed <= 0:
        raise ValueError(f"{label} must be greater than zero.")
    return parsed


def parse_nonnegative_decimal(value, label):
    try:
        parsed = Decimal(value or "0")
    except (InvalidOperation, TypeError) as exc:
        raise ValueError(f"{label} must be a valid number.") from exc
    if not parsed.is_finite() or parsed < 0:
        raise ValueError(f"{label} cannot be negative.")
    return parsed


def parse_nonnegative_int(value, label):
    try:
        parsed = int(value or "0")
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be a whole number.") from exc
    if parsed < 0:
        raise ValueError(f"{label} cannot be negative.")
    return parsed


def password_matches(stored_password, candidate):
    """Support old records once, then upgrade them after successful login."""
    if stored_password.startswith(("scrypt:", "pbkdf2:")):
        return check_password_hash(stored_password, candidate)
    return hmac.compare_digest(stored_password, candidate)


def credential_query(role, where):
    config = ROLE_CONFIG[role]
    return (
        f"SELECT {config['id']} AS user_id, {config['username']} AS username, "
        f"{config['password']} AS password_hash FROM {config['table']} WHERE {where}"
    )


@app2.route("/")
def home():
    return redirect(url_for("sepm" if session.get("user_id") else "login"))


@app2.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if session.get("user_id"):
            return redirect(url_for("sepm"))
        return render_template("login.html")

    role = request.form.get("role", "").lower()
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    try:
        employee_id = parse_positive_int(request.form.get("e_id"), "Employee ID")
        if role not in ROLE_CONFIG or not username or not password:
            raise ValueError("Complete every login field.")
    except ValueError as exc:
        flash(str(exc), "danger")
        return render_template("login.html"), 400

    config = ROLE_CONFIG[role]
    rows = execute_db(
        credential_query(role, f"{config['id']} = %s AND {config['username']} = %s"),
        (employee_id, username),
    )
    if len(rows) != 1 or not password_matches(rows[0]["password_hash"], password):
        flash("Invalid ID, username, password, or role.", "danger")
        return render_template("login.html"), 401

    stored_password = rows[0]["password_hash"]
    if not stored_password.startswith(("scrypt:", "pbkdf2:")):
        execute_db(
            f"UPDATE {config['table']} SET {config['password']} = %s WHERE {config['id']} = %s",
            (generate_password_hash(password), employee_id),
            commit=True,
        )

    session.clear()
    session.update(user_id=employee_id, username=username, role=role)
    return redirect(url_for("sepm"))


@app2.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


@app2.route("/registration", methods=["GET", "POST"])
def registration():
    if request.method == "GET":
        return render_template("registration.html")

    role = request.form.get("role", "employee").lower()
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    if role == "admin" and session.get("role") != "admin":
        abort(403)

    try:
        employee_id = parse_positive_int(request.form.get("e_id"), "Employee ID")
        if role not in ROLE_CONFIG:
            raise ValueError("Choose a valid role.")
        if not 3 <= len(username) <= 100:
            raise ValueError("Username must contain 3 to 100 characters.")
        if len(password) < 8:
            raise ValueError("Password must contain at least 8 characters.")
    except ValueError as exc:
        flash(str(exc), "danger")
        return render_template("registration.html"), 400

    if not execute_db("SELECT id FROM official WHERE id = %s", (employee_id,)):
        flash("Add the employee record before creating a login.", "danger")
        return render_template("registration.html"), 400

    config = ROLE_CONFIG[role]
    existing = execute_db(
        f"SELECT {config['id']} FROM {config['table']} "
        f"WHERE {config['id']} = %s OR {config['username']} = %s",
        (employee_id, username),
    )
    if existing:
        flash("That employee already has an account, or the username is taken.", "danger")
        return render_template("registration.html"), 409

    execute_db(
        f"INSERT INTO {config['table']} "
        f"({config['id']}, {config['username']}, {config['password']}) VALUES (%s, %s, %s)",
        (employee_id, username, generate_password_hash(password)),
        commit=True,
    )
    flash("Registration complete. You can now log in.", "success")
    return redirect(url_for("login"))


@app2.cli.command("create-admin")
@click.argument("employee_id", type=int)
@click.option("--username", prompt=True)
@click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
def create_admin(employee_id, username, password):
    """Create the first administrator without exposing public admin registration."""
    if len(username.strip()) < 3 or len(password) < 8:
        raise click.ClickException("Username needs 3 characters; password needs 8.")
    if not execute_db("SELECT id FROM official WHERE id = %s", (employee_id,)):
        raise click.ClickException("No official employee record has that ID.")
    if execute_db(
        "SELECT admin_id FROM admin_login WHERE admin_id = %s OR admin_username = %s",
        (employee_id, username.strip()),
    ):
        raise click.ClickException("That administrator ID or username already exists.")
    execute_db(
        "INSERT INTO admin_login (admin_id, admin_username, admin_password) VALUES (%s, %s, %s)",
        (employee_id, username.strip(), generate_password_hash(password)),
        commit=True,
    )
    click.echo("Administrator created.")


@app2.route("/sepm")
@login_required
def sepm():
    return render_template("index.html")


# Official employee records
@app2.route("/official")
@admin_required
def official():
    rows = execute_db("SELECT * FROM official ORDER BY id")
    return render_template("official.html", rows=rows)


@app2.route("/add_employee", methods=["POST"])
@admin_required
def add_employee():
    data = request.form
    try:
        employee_id = parse_positive_int(data.get("id"), "Employee ID")
        salary = parse_nonnegative_decimal(data.get("monthly_salary"), "Monthly salary")
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("official"))
    execute_db(
        """INSERT INTO official
        (id, name, join_date, designation, department, monthly_salary, email, phone_num)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
        (
            employee_id, data.get("name", "").strip(), data.get("join_date"),
            data.get("designation", "").strip(), data.get("department", "").strip(),
            salary, data.get("email", "").strip(), data.get("phone_num", "").strip(),
        ),
        commit=True,
    )
    flash("Employee added.", "success")
    return redirect(url_for("official"))


@app2.route("/update_employee", methods=["POST"])
@admin_required
def update_employee():
    data = request.form
    try:
        employee_id = parse_positive_int(data.get("e_id"), "Employee ID")
        salary = parse_nonnegative_decimal(data.get("monthly_salary"), "Monthly salary")
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("official"))
    execute_db(
        """UPDATE official SET name=%s, email=%s, phone_num=%s, department=%s,
        designation=%s, monthly_salary=%s WHERE id=%s""",
        (
            data.get("name", "").strip(), data.get("email", "").strip(),
            data.get("phone", "").strip(), data.get("department", "").strip(),
            data.get("designation", "").strip(), salary, employee_id,
        ),
        commit=True,
    )
    flash("Employee updated.", "success")
    return redirect(url_for("official"))


@app2.route("/delete_employee/<int:emp_id>", methods=["POST"])
@admin_required
def delete_employee(emp_id):
    if emp_id == session["user_id"]:
        flash("You cannot delete the account you are currently using.", "danger")
        return redirect(url_for("official"))
    conn = get_db()
    cursor = None
    try:
        cursor = conn.cursor()
        for table, column in (
            ("salary", "emp_id"), ("attendance", "emp_id"), ("leaves", "emp_id"),
            ("admin_login", "admin_id"), ("emp_login", "emp_id"),
        ):
            cursor.execute(f"DELETE FROM {table} WHERE {column} = %s", (emp_id,))
        cursor.execute("DELETE FROM official WHERE id = %s", (emp_id,))
        conn.commit()
        flash("Employee and related records deleted.", "success")
    except Error:
        conn.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()
    return redirect(url_for("official"))


# Salary records
@app2.route("/salary")
@admin_required
def salary():
    rows = execute_db(
        """SELECT official.id AS emp_id, official.name, salary.monthly_salary,
        salary.bonus, salary.deduction FROM salary
        JOIN official ON salary.emp_id = official.id ORDER BY official.id"""
    )
    return render_template("salary.html", rows=rows)


def salary_values(data):
    return (
        parse_nonnegative_decimal(data.get("monthly_salary"), "Monthly salary"),
        parse_nonnegative_decimal(data.get("bonus"), "Bonus"),
        parse_nonnegative_decimal(data.get("deduction"), "Deduction"),
    )


@app2.route("/add_salary", methods=["POST"])
@admin_required
def add_salary():
    try:
        employee_id = parse_positive_int(request.form.get("emp_id"), "Employee ID")
        values = salary_values(request.form)
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("salary"))
    execute_db(
        "INSERT INTO salary (emp_id, monthly_salary, bonus, deduction) VALUES (%s, %s, %s, %s)",
        (employee_id, *values), commit=True,
    )
    flash("Salary record added.", "success")
    return redirect(url_for("salary"))


@app2.route("/update_salary", methods=["POST"])
@admin_required
def update_salary():
    try:
        employee_id = parse_positive_int(request.form.get("emp_id"), "Employee ID")
        values = salary_values(request.form)
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("salary"))
    execute_db(
        "UPDATE salary SET monthly_salary=%s, bonus=%s, deduction=%s WHERE emp_id=%s",
        (*values, employee_id), commit=True,
    )
    flash("Salary record updated.", "success")
    return redirect(url_for("salary"))


@app2.route("/delete_salary/<int:emp_id>", methods=["POST"])
@admin_required
def delete_salary(emp_id):
    execute_db("DELETE FROM salary WHERE emp_id = %s", (emp_id,), commit=True)
    flash("Salary record deleted.", "success")
    return redirect(url_for("salary"))


# Attendance records
@app2.route("/attendance")
@admin_required
def attendance():
    rows = execute_db(
        """SELECT official.id AS emp_id, official.name, attendance.entry_time,
        attendance.exit_time FROM attendance
        JOIN official ON attendance.emp_id = official.id ORDER BY official.id"""
    )
    return render_template("attendance.html", rows=rows)


@app2.route("/add_attendance", methods=["POST"])
@admin_required
def add_attendance():
    try:
        employee_id = parse_positive_int(request.form.get("emp_id"), "Employee ID")
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("attendance"))
    execute_db(
        "INSERT INTO attendance (emp_id, entry_time, exit_time) VALUES (%s, %s, %s)",
        (employee_id, request.form.get("entry_time") or None, request.form.get("exit_time") or None),
        commit=True,
    )
    flash("Attendance record added.", "success")
    return redirect(url_for("attendance"))


@app2.route("/update_attendance", methods=["POST"])
@admin_required
def update_attendance():
    try:
        employee_id = parse_positive_int(request.form.get("emp_id"), "Employee ID")
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("attendance"))
    execute_db(
        "UPDATE attendance SET entry_time=%s, exit_time=%s WHERE emp_id=%s",
        (request.form.get("entry_time") or None, request.form.get("exit_time") or None, employee_id),
        commit=True,
    )
    flash("Attendance record updated.", "success")
    return redirect(url_for("attendance"))


@app2.route("/delete_attendance/<int:emp_id>", methods=["POST"])
@admin_required
def delete_attendance(emp_id):
    execute_db("DELETE FROM attendance WHERE emp_id = %s", (emp_id,), commit=True)
    flash("Attendance record deleted.", "success")
    return redirect(url_for("attendance"))


@app2.route("/update_entry", methods=["POST"])
@admin_required
def entry_time():
    execute_db(
        "UPDATE attendance SET entry_time=%s WHERE emp_id=%s",
        (request.form.get("entry"), request.form.get("e_id")), commit=True,
    )
    flash("Entry time updated.", "success")
    return redirect(url_for("attendance"))


@app2.route("/update_exit", methods=["POST"])
@admin_required
def exit_time():
    execute_db(
        "UPDATE attendance SET exit_time=%s WHERE emp_id=%s",
        (request.form.get("exittime"), request.form.get("e_id")), commit=True,
    )
    flash("Exit time updated.", "success")
    return redirect(url_for("attendance"))


# Leave records
@app2.route("/leaves")
@admin_required
def leaves():
    rows = execute_db(
        """SELECT official.id AS emp_id, official.name, leaves.leaves_allowed,
        leaves.leaves_taken, leaves.leaves_left FROM leaves
        JOIN official ON leaves.emp_id = official.id ORDER BY official.id"""
    )
    return render_template("leaves.html", rows=rows)


def leave_values(data):
    allowed = parse_nonnegative_int(data.get("leaves_allowed"), "Leaves allowed")
    taken = parse_nonnegative_int(data.get("leaves_taken"), "Leaves taken")
    left = parse_nonnegative_int(data.get("leaves_left"), "Leaves left")
    if taken + left != allowed:
        raise ValueError("Leaves taken plus leaves left must equal leaves allowed.")
    return allowed, taken, left


@app2.route("/add_leaves", methods=["POST"])
@admin_required
def add_leaves():
    try:
        employee_id = parse_positive_int(request.form.get("emp_id"), "Employee ID")
        values = leave_values(request.form)
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("leaves"))
    execute_db(
        "INSERT INTO leaves (emp_id, leaves_allowed, leaves_taken, leaves_left) VALUES (%s, %s, %s, %s)",
        (employee_id, *values), commit=True,
    )
    flash("Leave record added.", "success")
    return redirect(url_for("leaves"))


@app2.route("/update_leaves", methods=["POST"])
@admin_required
def update_leaves():
    try:
        employee_id = parse_positive_int(request.form.get("emp_id"), "Employee ID")
        values = leave_values(request.form)
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("leaves"))
    execute_db(
        "UPDATE leaves SET leaves_allowed=%s, leaves_taken=%s, leaves_left=%s WHERE emp_id=%s",
        (*values, employee_id), commit=True,
    )
    flash("Leave record updated.", "success")
    return redirect(url_for("leaves"))


@app2.route("/delete_leaves/<int:emp_id>", methods=["POST"])
@admin_required
def delete_leaves(emp_id):
    execute_db("DELETE FROM leaves WHERE emp_id = %s", (emp_id,), commit=True)
    flash("Leave record deleted.", "success")
    return redirect(url_for("leaves"))


# Current user's credentials
@app2.route("/login_cred")
@login_required
def login_cred():
    config = ROLE_CONFIG[session["role"]]
    rows = execute_db(
        f"SELECT {config['id']} AS emp_id, {config['username']} AS emp_username "
        f"FROM {config['table']} WHERE {config['id']} = %s",
        (session["user_id"],),
    )
    return render_template("login_cred.html", rows=rows)


@app2.route("/editusername", methods=["POST"])
@login_required
def edit_uname():
    username = request.form.get("username", "").strip()
    if not 3 <= len(username) <= 100:
        flash("Username must contain 3 to 100 characters.", "danger")
        return redirect(url_for("login_cred"))
    config = ROLE_CONFIG[session["role"]]
    if execute_db(
        f"SELECT {config['id']} FROM {config['table']} WHERE {config['username']} = %s",
        (username,),
    ):
        flash("That username is already taken.", "danger")
        return redirect(url_for("login_cred"))
    execute_db(
        f"UPDATE {config['table']} SET {config['username']}=%s WHERE {config['id']}=%s",
        (username, session["user_id"]), commit=True,
    )
    session["username"] = username
    flash("Username updated.", "success")
    return redirect(url_for("login_cred"))


@app2.route("/editpwd", methods=["POST"])
@login_required
def edit_pwd():
    current_password = request.form.get("current_password", "")
    password = request.form.get("password", "")
    confirmation = request.form.get("confirm_password", "")
    if len(password) < 8 or password != confirmation:
        flash("Use at least 8 characters and enter matching new passwords.", "danger")
        return redirect(url_for("login_cred"))
    config = ROLE_CONFIG[session["role"]]
    rows = execute_db(
        credential_query(session["role"], f"{config['id']} = %s"),
        (session["user_id"],),
    )
    if len(rows) != 1 or not password_matches(rows[0]["password_hash"], current_password):
        flash("The current password is incorrect.", "danger")
        return redirect(url_for("login_cred"))
    execute_db(
        f"UPDATE {config['table']} SET {config['password']}=%s WHERE {config['id']}=%s",
        (generate_password_hash(password), session["user_id"]), commit=True,
    )
    flash("Password updated.", "success")
    return redirect(url_for("login_cred"))


# Backward-compatible endpoints used by the official-details page
@app2.route("/edit_name", methods=["POST"])
@admin_required
def name():
    execute_db("UPDATE official SET name=%s WHERE id=%s", (request.form.get("name"), request.form.get("e_id")), commit=True)
    flash("Name updated.", "success")
    return redirect(url_for("official"))


@app2.route("/edit_email", methods=["POST"])
@admin_required
def emailid():
    execute_db("UPDATE official SET email=%s WHERE id=%s", (request.form.get("email"), request.form.get("e_id")), commit=True)
    flash("Email updated.", "success")
    return redirect(url_for("official"))


@app2.route("/edit_phone", methods=["POST"])
@admin_required
def phonenum():
    execute_db("UPDATE official SET phone_num=%s WHERE id=%s", (request.form.get("phone"), request.form.get("e_id")), commit=True)
    flash("Phone number updated.", "success")
    return redirect(url_for("official"))


@app2.errorhandler(400)
def bad_request(error):
    return str(getattr(error, "description", "Bad request.")), 400


@app2.errorhandler(403)
def forbidden(error):
    return "You do not have permission to access this page.", 403


@app2.errorhandler(Error)
def database_error(error):
    return "A database error occurred. Check the server log and database configuration.", 500


if __name__ == "__main__":
    app2.run(debug=os.environ.get("FLASK_DEBUG") == "1")
