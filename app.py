
import os
from decimal import Decimal, InvalidOperation
from functools import wraps

from dotenv import load_dotenv
from flask import (
    Flask,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_wtf.csrf import CSRFProtect
from mysql.connector import Error, IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from db import get_db


load_dotenv()

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY")
if not app.config["SECRET_KEY"]:
    raise RuntimeError("Add FLASK_SECRET_KEY to your .env file")

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = (
    os.getenv("COOKIE_SECURE", "false").lower() == "true"
)

csrf = CSRFProtect(app)


# --------------------------------------------------
# LOGIN REQUIRED DECORATOR
# --------------------------------------------------

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user_id = session.get("user_id")

        if not user_id:
            flash("Please log in first.", "warning")
            return redirect(url_for("login"))

        conn = None
        cursor = None

        try:
            conn = get_db()
            cursor = conn.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT u.id, u.email, u.organization_id, o.name
                FROM users u
                JOIN organizations o ON o.id = u.organization_id
                WHERE u.id = %s
                """,
                (user_id,),
            )

            g.user = cursor.fetchone()

        except Error:
            app.logger.exception("Failed to load user")
            flash("Unable to load your account.", "error")
            return redirect(url_for("login"))

        finally:
            if cursor:
                cursor.close()

            if conn and conn.is_connected():
                conn.close()

        if not g.user:
            session.clear()
            return redirect(url_for("login"))

        return view(*args, **kwargs)

    return wrapped


# --------------------------------------------------
# PRODUCT FORM VALIDATION
# --------------------------------------------------

def parse_price(field_name):
    """Return a Decimal price or None for an empty field."""

    value = request.form.get(field_name, "").strip()

    if not value:
        return None

    price = Decimal(value)

    if (
        not price.is_finite()
        or price < 0
        or price > Decimal("99999999.99")
        or price.as_tuple().exponent < -2
    ):
        raise ValueError(f"Invalid {field_name}")

    return price


def read_product_form():
    """Validate product fields and return them as a dictionary."""

    name = request.form.get("name", "").strip()
    sku = request.form.get("sku", "").strip()
    description = request.form.get("description", "").strip() or None

    if not name or len(name) > 150:
        raise ValueError("Enter a product name up to 150 characters.")

    if not sku or len(sku) > 100:
        raise ValueError("Enter an SKU up to 100 characters.")

    quantity = int(request.form.get("quantity", "0"))

    if quantity < 0:
        raise ValueError("Quantity cannot be negative.")

    threshold_text = request.form.get(
        "low_stock_threshold", ""
    ).strip()

    threshold = int(threshold_text) if threshold_text else None

    if threshold is not None and threshold < 0:
        raise ValueError("Low-stock threshold cannot be negative.")

    return {
        "name": name,
        "sku": sku,
        "description": description,
        "quantity": quantity,
        "cost_price": parse_price("cost_price"),
        "selling_price": parse_price("selling_price"),
        "low_stock_threshold": threshold,
    }


# --------------------------------------------------
# HOME
# --------------------------------------------------

@app.route("/")
def home():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))

    return redirect(url_for("login"))


# --------------------------------------------------
# SIGNUP
# --------------------------------------------------

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        org_name = request.form.get("organization_name", "").strip()

        if not email or len(email) > 255 or "@" not in email:
            flash("Enter a valid email address.", "error")
            return render_template("signup.html")

        if not org_name or len(org_name) > 150:
            flash("Enter a valid organization name.", "error")
            return render_template("signup.html")

        if len(password) < 8:
            flash("Password must be at least 8 characters.", "error")
            return render_template("signup.html")

        if password != confirm:
            flash("Passwords do not match.", "error")
            return render_template("signup.html")

        conn = None
        cursor = None

        try:
            password_hash = generate_password_hash(password)

            conn = get_db()
            conn.start_transaction()
            cursor = conn.cursor()

            cursor.execute(
                "INSERT INTO organizations (name) VALUES (%s)",
                (org_name,),
            )

            org_id = cursor.lastrowid

            cursor.execute(
                """
                INSERT INTO users
                    (organization_id, email, password_hash)
                VALUES (%s, %s, %s)
                """,
                (org_id, email, password_hash),
            )

            user_id = cursor.lastrowid
            conn.commit()

            session.clear()
            session["user_id"] = user_id

            flash("Account created successfully!", "success")
            return redirect(url_for("dashboard"))

        except IntegrityError:
            if conn and conn.is_connected():
                conn.rollback()

            flash("This email is already registered.", "error")

        except Error:
            if conn and conn.is_connected():
                conn.rollback()

            app.logger.exception("Signup database error")
            flash("Unable to create your account.", "error")

        finally:
            if cursor:
                cursor.close()

            if conn and conn.is_connected():
                conn.close()

    return render_template("signup.html")


# --------------------------------------------------
# LOGIN
# --------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        conn = None
        cursor = None

        try:
            conn = get_db()
            cursor = conn.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT id, password_hash
                FROM users
                WHERE email = %s
                """,
                (email,),
            )

            user = cursor.fetchone()

            if user and check_password_hash(
                user["password_hash"], password
            ):
                session.clear()
                session["user_id"] = user["id"]

                flash("Login successful!", "success")
                return redirect(url_for("dashboard"))

            flash("Invalid email or password.", "error")

        except Error:
            app.logger.exception("Login database error")
            flash("Unable to log in right now.", "error")

        finally:
            if cursor:
                cursor.close()

            if conn and conn.is_connected():
                conn.close()

    return render_template("login.html")


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------
    
@app.route("/dashboard")
@login_required
def dashboard():
    conn = None
    cursor = None
    product_count = 0
    total_units = 0
    low_stock_count = 0
    low_stock_products = []

    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                COUNT(*) AS product_count,
                COALESCE(SUM(quantity), 0) AS total_units,
                COALESCE(SUM(
                    CASE
                        WHEN low_stock_threshold IS NOT NULL
                         AND quantity <= low_stock_threshold
                        THEN 1 ELSE 0
                    END
                ), 0) AS low_stock_count
            FROM products
            WHERE organization_id = %s
            """,
            (g.user["organization_id"],),
        )

        summary = cursor.fetchone() or {}
        product_count = summary.get("product_count", 0)
        total_units = summary.get("total_units", 0)
        low_stock_count = summary.get("low_stock_count", 0)

        cursor.execute(
            """
            SELECT id, name, sku, quantity, low_stock_threshold
            FROM products
            WHERE organization_id = %s
              AND low_stock_threshold IS NOT NULL
              AND quantity <= low_stock_threshold
            ORDER BY quantity ASC, name ASC
            LIMIT 8
            """,
            (g.user["organization_id"],),
        )

        low_stock_products = cursor.fetchall()

    except Error:
        app.logger.exception("Failed to load dashboard")
        flash("Unable to load the dashboard summary.", "error")

    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

    return render_template(
        "dashboard.html",
        user=g.user,
        product_count=product_count,
        total_units=total_units,
        low_stock_count=low_stock_count,
        low_stock_products=low_stock_products,
    )

    return render_template("dashboard.html", user=g.user)


# --------------------------------------------------
# ADD AND DISPLAY PRODUCTS
# --------------------------------------------------

@app.route("/products", methods=["GET", "POST"])
@login_required
def products():
    if request.method == "POST":
        try:
            data = read_product_form()

        except (ValueError, InvalidOperation):
            flash(
                "Check the product name, SKU, quantity, prices, "
                "and low-stock threshold.",
                "error",
            )
            return redirect(url_for("products"))

        conn = None
        cursor = None

        try:
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO products
                    (
                        organization_id,
                        name,
                        sku,
                        description,
                        quantity,
                        cost_price,
                        selling_price,
                        low_stock_threshold
                    )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    g.user["organization_id"],
                    data["name"],
                    data["sku"],
                    data["description"],
                    data["quantity"],
                    data["cost_price"],
                    data["selling_price"],
                    data["low_stock_threshold"],
                ),
            )

            conn.commit()
            flash("Product added successfully!", "success")

        except IntegrityError:
            if conn and conn.is_connected():
                conn.rollback()

            flash(
                "This SKU already exists in your organization's inventory.",
                "error",
            )

        except Error:
            if conn and conn.is_connected():
                conn.rollback()

            app.logger.exception("Failed to add product")
            flash("Unable to save the product.", "error")

        finally:
            if cursor:
                cursor.close()

            if conn and conn.is_connected():
                conn.close()

        return redirect(url_for("products"))

    conn = None
    cursor = None
    product_list = []

    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                id,
                name,
                sku,
                description,
                quantity,
                cost_price,
                selling_price,
                low_stock_threshold
            FROM products
            WHERE organization_id = %s
            ORDER BY id DESC
            """,
            (g.user["organization_id"],),
        )

        product_list = cursor.fetchall()

    except Error:
        app.logger.exception("Failed to load products")
        flash("Unable to load products.", "error")

    finally:
        if cursor:
            cursor.close()

        if conn and conn.is_connected():
            conn.close()

    return render_template(
        "products.html",
        products=product_list,
    )


# --------------------------------------------------
# EDIT PRODUCT
# --------------------------------------------------

@app.route(
    "/products/<int:product_id>/edit",
    methods=["GET", "POST"],
)
@login_required
def edit_product(product_id):
    conn = None
    cursor = None

    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                id,
                name,
                sku,
                description,
                quantity,
                cost_price,
                selling_price,
                low_stock_threshold
            FROM products
            WHERE id = %s AND organization_id = %s
            """,
            (product_id, g.user["organization_id"]),
        )

        product = cursor.fetchone()

        if not product:
            abort(404)

        if request.method == "POST":
            try:
                data = read_product_form()

            except (ValueError, InvalidOperation):
                flash(
                    "Check the product name, SKU, quantity, prices, "
                    "and low-stock threshold.",
                    "error",
                )

                return redirect(
                    url_for(
                        "edit_product",
                        product_id=product_id,
                    )
                )

            cursor.execute(
                """
                UPDATE products
                SET
                    name = %s,
                    sku = %s,
                    description = %s,
                    quantity = %s,
                    cost_price = %s,
                    selling_price = %s,
                    low_stock_threshold = %s
                WHERE id = %s AND organization_id = %s
                """,
                (
                    data["name"],
                    data["sku"],
                    data["description"],
                    data["quantity"],
                    data["cost_price"],
                    data["selling_price"],
                    data["low_stock_threshold"],
                    product_id,
                    g.user["organization_id"],
                ),
            )

            conn.commit()

            flash("Product updated successfully!", "success")
            return redirect(url_for("products"))

        return render_template(
            "edit_product.html",
            product=product,
        )

    except IntegrityError:
        if conn and conn.is_connected():
            conn.rollback()

        flash("That SKU is already in use.", "error")
        return redirect(url_for("products"))

    except Error:
        if conn and conn.is_connected():
            conn.rollback()

        app.logger.exception("Failed to edit product")
        flash("Unable to update the product.", "error")
        return redirect(url_for("products"))

    finally:
        if cursor:
            cursor.close()

        if conn and conn.is_connected():
            conn.close()


# --------------------------------------------------
# DELETE PRODUCT
# --------------------------------------------------

@app.route(
    "/products/<int:product_id>/delete",
    methods=["POST"],
)
@login_required
def delete_product(product_id):
    conn = None
    cursor = None

    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute(
            """
            DELETE FROM products
            WHERE id = %s AND organization_id = %s
            """,
            (product_id, g.user["organization_id"]),
        )

        deleted = cursor.rowcount
        conn.commit()

        if deleted:
            flash("Product deleted successfully!", "success")
        else:
            flash("Product not found.", "warning")

    except Error:
        if conn and conn.is_connected():
            conn.rollback()

        app.logger.exception("Failed to delete product")
        flash("Unable to delete the product.", "error")

    finally:
        if cursor:
            cursor.close()

        if conn and conn.is_connected():
            conn.close()

    return redirect(url_for("products"))


# --------------------------------------------------
# LOGOUT
# --------------------------------------------------

@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("login"))


# --------------------------------------------------
# RUN APPLICATION
# --------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)
