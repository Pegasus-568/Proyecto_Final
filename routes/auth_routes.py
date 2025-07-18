from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from models.user import User
from DB import get_connection
import bcrypt

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"].encode("utf-8")

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user_data = cursor.fetchone()
        conn.close()

        if user_data and bcrypt.checkpw(password, user_data["password"].encode("utf-8")):
            user = User(user_data["id"], user_data["username"], user_data["password"], user_data["rol"])
            login_user(user)
            if user.rol == "admin":
                return redirect("/admin")
            else:
                return redirect("/consultar")
        else:
            flash("Credenciales inválidas", "danger")

    return render_template("login.html")

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))