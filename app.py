import json
import os
from datetime import date, datetime
from functools import wraps
from uuid import uuid4

from flask import Flask, flash, redirect, render_template, request, session, url_for


app = Flask(__name__)
app.secret_key = "samxpress-development-secret"
DATA_FILE = os.path.join(os.path.dirname(__file__), "data.json")
STATUSES = ["Requested", "Allocated", "Collected", "In transit", "Delivered"]


def load_data():
    try:
        with open(DATA_FILE, encoding="utf-8") as data_file:
            return json.load(data_file)
    except Exception:
        return {"deliveries": [], "drivers": [], "vehicles": []}


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as data_file:
        json.dump(data, data_file, indent=2)


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped_view


@app.before_request
def require_login():
    if request.endpoint not in {"login", "static"} and not session.get("logged_in"):
        return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("username") == "dispatch" and request.form.get("password") == "samxpress123":
            session["logged_in"] = True
            return redirect(url_for("index"))
        flash("Those sign-in details were not recognised.", "error")
    current_hour = datetime.now().hour
    greeting = "Good morning" if current_hour < 12 else "Good afternoon" if current_hour < 18 else "Good evening"
    return render_template("login.html", greeting=greeting)


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index():
    data = load_data()
    map(
        lambda delivery: delivery.update(
            {
                "is_overdue": delivery.get("due_date", "") < date.today().isoformat()
                and delivery.get("status") != "Delivered"
            }
        ),
        data["deliveries"],
    )
    deliveries = sorted(data["deliveries"], key=lambda delivery: delivery.get("due_date", ""))
    counts = {status: sum(item.get("status") == status for item in deliveries) for status in STATUSES}
    return render_template(
        "index.html",
        deliveries=deliveries,
        drivers=data["drivers"],
        vehicles=data["vehicles"],
        statuses=STATUSES,
        counts=counts,
        active_count=sum(item.get("status") != "Delivered" for item in deliveries),
    )


@app.route("/deliveries", methods=["POST"])
@login_required
def create_delivery():
    data = load_data()
    delivery = {
        "id": str(uuid4())[:8].upper(),
        "customer": request.form.get("customer", "").strip(),
        "item": request.form.get("item", "").strip(),
        "pickup": request.form.get("pickup", "").strip(),
        "dropoff": request.form.get("dropoff", "").strip(),
        "due_date": request.form.get("due_date", ""),
        "distance_miles": request.form.get("distance_miles", ""),
        "status": "Requested",
        "driver_id": "",
        "vehicle_id": "",
    }
    data["deliveries"].insert(0, delivery)
    save_data(data)
    flash(f"Delivery {delivery['id']} added to the run list.", "success")
    return redirect(url_for("index"))


@app.route("/deliveries/<delivery_id>/assign", methods=["POST"])
@login_required
def assign_delivery(delivery_id):
    data = load_data()
    delivery = next((item for item in data["deliveries"] if item["id"] == delivery_id), None)
    if delivery:
        delivery["driver_id"] = request.form.get("driver_id", "")
        delivery["vehicle_id"] = request.form.get("vehicle_id", "")
        if delivery["driver_id"] or delivery["vehicle_id"]:
            delivery["status"] = "Allocated"
        save_data(data)
        flash(f"Assignment updated for {delivery_id}.", "success")
    return redirect(url_for("index"))


@app.route("/deliveries/<delivery_id>/status", methods=["POST"])
@login_required
def update_status(delivery_id):
    data = load_data()
    delivery = next((item for item in data["deliveries"] if item["id"] == delivery_id), None)
    if delivery:
        delivery["status"] = request.form.get("status", delivery["status"])
        save_data(data)
        flash(f"Status updated for {delivery_id}.", "success")
    return redirect(url_for("index"))


@app.route("/deliveries/<delivery_id>/delete")
@login_required
def delete_delivery(delivery_id):
    data = load_data()
    data["deliveries"] = [item for item in data["deliveries"] if item["id"] != delivery_id]
    save_data(data)
    flash(f"Delivery {delivery_id} removed.", "success")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)