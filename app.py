from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime
from flask import abort
import re
import json
import os
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.secret_key = 'takeaway_secret'

# File paths
USERS_FILE = 'users.json'
MENU_FILE = 'menu.json'
ABOUT_US_FILE = 'about_us.json'

ORDERS_FILE = 'orders.json'
CART_FILE = 'carts.json'
ORDER_COUNTER_FILE = 'order_counter.json'
DELIVERY_STATUS_FILE = 'delivery_status.json'

def load_delivery_status():
    if os.path.exists(DELIVERY_STATUS_FILE):
        with open(DELIVERY_STATUS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_delivery_status(status_data):
    with open(DELIVERY_STATUS_FILE, 'w') as f:
        json.dump(status_data, f, indent=4)


# OTP storage in memory
otp_storage = {}

def load_order_counter():
    today = str(date.today())
    if os.path.exists(ORDER_COUNTER_FILE):
        with open(ORDER_COUNTER_FILE, 'r') as f:
            data = json.load(f)
            return data.get(today, 0)
    return 0

def save_order_counter(new_id):
    today = str(date.today())
    data = {}
    if os.path.exists(ORDER_COUNTER_FILE):
        with open(ORDER_COUNTER_FILE, 'r') as f:
            data = json.load(f)
    data[today] = new_id
    with open(ORDER_COUNTER_FILE, 'w') as f:
        json.dump(data, f, indent=4)



def load_carts():
    if os.path.exists(CART_FILE):
        with open(CART_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_carts(carts):
    with open(CART_FILE, 'w') as f:
        json.dump(carts, f, indent=4)


def load_orders():
    if not os.path.exists('orders.json'):
        return {}  # This is correct if the file doesn't exist
    with open('orders.json', 'r') as f:
        return json.load(f)




def save_orders(orders):
    with open('orders.json', 'w') as f:
        json.dump(orders, f, indent=4)



# Load users from file
def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, 'r') as f:
        return json.load(f)
# Save users to file
def save_users(users_data):
    with open(USERS_FILE, 'w') as f:
        json.dump(users_data, f, indent=4)


# Default menu data
default_menu_items = {
    "Main Course": [
        {"name": "Veg Biryani", "price": 120, "quantity": 0},
        {"name": "Chicken Biryani", "price": 160, "quantity": 0},
        {"name": "Mutton Biryani", "price": 200, "quantity": 0},
        {"name": "Paneer Butter Masala", "price": 140, "quantity": 0},
        {"name": "Butter Chicken", "price": 180, "quantity": 0},
        {"name": "Fish Curry", "price": 180, "quantity": 0},
        {"name": "Dal Tadka", "price": 90, "quantity": 0},
        {"name": "Kadai Paneer", "price": 150, "quantity": 0},
        {"name": "Egg Curry", "price": 110, "quantity": 0},
        {"name": "Jeera Rice", "price": 70, "quantity": 0}
    ],
    # ... (other categories as you already had)
}
def load_menu():
    if os.path.exists(MENU_FILE):
        with open(MENU_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_menu(menu_data):
    with open(MENU_FILE, 'w') as f:
        json.dump(menu_data, f, indent=4)

menu_items = load_menu()

def load_about_us():
    if os.path.exists(ABOUT_US_FILE):
        with open(ABOUT_US_FILE, 'r') as f:
            return json.load(f)
    return {"description": "", "phone": "", "email": ""}

def save_about_us(data):
    with open(ABOUT_US_FILE, 'w') as f:
        json.dump(data, f, indent=4)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        users = load_users()  # ✅ move inside function

        email = request.form['email'].strip().lower()
        password = request.form['password']

        email_regex = r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$'
        password_regex = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$'

        if not re.match(email_regex, email):
            flash("Invalid email format.", "error")
            return redirect(url_for('signup'))

        if not re.match(password_regex, password):
            flash("Password must meet complexity requirements.", "error")
            return redirect(url_for('signup'))

        if email in users:
            flash("Email already registered.", "error")
            return redirect(url_for('login'))

        users[email] = {"password": password}
        save_users(users)
        flash("Signup successful. Please login.", "success")
        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        users = load_users()  # ✅ move inside function

        email = request.form['email'].strip().lower()
        password = request.form['password']

        session.clear()  # Good!

        if email == 'admin123@gmail.com' and password == 'Admin@123':
            session['user'] = email
            session['is_admin'] = True
            return redirect(url_for('admin_dashboard'))

        user = users.get(email)
        if user and user['password'] == password:
            session['user'] = email
            session['is_admin'] = False

            if email.endswith('@delivery.com'):
                session['is_delivery'] = True
                status_data = load_delivery_status()
                status_data[email] = "free"
                save_delivery_status(status_data)
                return redirect(url_for('delivery_dashboard'))

            return redirect(url_for('user_dashboard'))

        flash("Invalid credentials.", "error")
        return redirect(url_for('login'))

    return render_template('login.html')



    return render_template('login.html')
@app.route('/admin_dashboard')
def admin_dashboard():
    if not session.get('is_admin'):
        return redirect(url_for('login'))

    orders = load_orders()
    return render_template('admin_dashboard.html', orders=orders)


@app.route('/user_dashboard')
def user_dashboard():
    if 'user' not in session or session.get('is_admin'):
        return redirect(url_for('login'))
    return render_template('user_dashboard.html', user=session['user'])

@app.route('/delivery_dashboard')
def delivery_dashboard():
    if not session.get('is_delivery'):
        return redirect(url_for('login'))

    user_email = session['user']
    orders = load_orders()
    assigned_orders = []

    for order_list in orders.values():
        for order in order_list:
            if order.get('delivery_person') == user_email:
                assigned_orders.append(order)

    return render_template('delivery_dashboard.html', orders=assigned_orders)

@app.route('/delivery_orders')
def delivery_orders():
    if 'user' not in session or not session.get('is_delivery'):
        return redirect(url_for('login'))

    delivery_email = session['user']
    all_orders = load_orders()

    # Add debug print statements
    print("All Orders:", all_orders)  # Debugging: Check the content of orders

    my_orders = []

    for user_email, orders in all_orders.items():
        for order in orders:
            if order.get("assigned_to") == delivery_email:
                order["email"] = user_email
                my_orders.append(order)

    return render_template('delivery_orders.html', user=session['user'], orders=my_orders)


@app.route('/menu')
def menu():
    if 'user' not in session:
        return redirect(url_for('login'))

    query = request.args.get('query', '').strip().lower()
    if query:
        filtered_items = {}
        for category, items in menu_items.items():
            filtered = [item for item in items if query in item['name'].lower()]
            if filtered:
                filtered_items[category] = filtered
    else:
        filtered_items = menu_items

    return render_template('menu.html', menu_items=filtered_items, search_query=query)

from datetime import date

@app.route('/admin/orders')
def orders():
    if 'user' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))

    today = str(date.today())

    with open('orders.json') as f:
        data = json.load(f)

    all_orders = []
    for user_email, user_orders in data.items():
        for order in user_orders:
            if order.get("date") == today:
                order["email"] = user_email
                all_orders.append(order)

    # ✅ Ensure FIFO by sorting by order_id
    all_orders.sort(key=lambda x: x['order_id'])

    return render_template('orders.html', orders=all_orders)

@app.route('/stocks', methods=['GET', 'POST'])
def stocks():
    if 'user' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))

    global menu_items

    if request.method == 'POST':
        category = request.form.get('category')
        name = request.form.get('name')
        try:
            new_price = int(request.form.get('price'))
            new_quantity = int(request.form.get('quantity'))
        except (TypeError, ValueError):
            flash("Invalid input for price or quantity.", "error")
            return redirect(url_for('stocks'))

        if category in menu_items:
            for item in menu_items[category]:
                if item['name'] == name:
                    item['price'] = new_price
                    item['quantity'] = new_quantity
                    save_menu(menu_items)  # Persist changes
                    flash(f"Updated {name} successfully.", "success")
                    break
        else:
            flash("Category not found.", "error")

        return redirect(url_for('stocks'))

    query = request.args.get('query', '').strip().lower()
    if query:
        filtered_items = {}
        for category, items in menu_items.items():
            filtered = [item for item in items if query in item['name'].lower()]
            if filtered:
                filtered_items[category] = filtered
    else:
        filtered_items = menu_items

    return render_template('stocks.html', menu_items=filtered_items, search_query=query)

# ------------------ About Us Routes ------------------
@app.route('/about_us')
def about_us():
    if 'user' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))

    about_us_data = load_about_us()
    return render_template('about_us.html', user=session['user'], about_us_data=about_us_data)

@app.route('/edit_about_us', methods=['POST'])
def edit_about_us():
    if 'user' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))

    data = {
        "description": request.form.get("description", ""),
        "phone": request.form.get("phone", ""),
        "email": request.form.get("email", "")
    }

    save_about_us(data)
    flash("About Us information updated successfully.", "success")
    return redirect(url_for('about_us'))

@app.route('/user_menu')
def user_menu():
    if 'user' not in session or session.get('is_admin'):
        return redirect(url_for('login'))

    query = request.args.get('query', '').strip().lower()
    menu_data = load_menu()  # Load the latest menu

    if query:
        filtered_items = {}
        for category, items in menu_data.items():
            matched = [item for item in items if query in item['name'].lower()]
            if matched:
                filtered_items[category] = matched
    else:
        filtered_items = menu_data

    return render_template('user_menu.html', user=session['user'], menu_items=filtered_items, search_query=query)

@app.route('/user_feedback')
def user_feedback():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('user_feedback.html', user=session['user'])

@app.route('/user_about_us')
def user_about_us():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('user_about_us.html', user=session['user'])

@app.route('/update_quantity/<item_name>', methods=['POST'])
def update_quantity(item_name):
    if 'user' not in session or session.get('is_admin'):
        return redirect(url_for('login'))

    action = request.form.get('action')
    user_email = session['user']
    carts = load_carts()
    cart = carts.get(user_email, [])

    updated = False
    for item in cart:
        if item['name'] == item_name:
            if action == 'increase':
                item['quantity'] += 1
            elif action == 'decrease':
                item['quantity'] = max(1, item['quantity'] - 1)
            updated = True
            break

    if updated:
        carts[user_email] = cart
        save_carts(carts)
    else:
        flash('Item not found in cart.', 'error')

    return redirect(url_for('view_cart'))


@app.route('/remove_from_cart/<item_name>')
def remove_from_cart(item_name):
    if 'user' not in session or session.get('is_admin'):
        return redirect(url_for('login'))

    user_email = session['user']
    carts = load_carts()
    cart = carts.get(user_email, [])

    original_len = len(cart)
    cart = [item for item in cart if item['name'] != item_name]

    if len(cart) < original_len:
        flash('Item removed from cart.', 'info')
    else:
        flash('Item not found in cart.', 'error')

    carts[user_email] = cart
    save_carts(carts)

    return redirect(url_for('view_cart'))


@app.route('/clear_cart')
def clear_cart():
    if 'user' not in session or session.get('is_admin'):
        return redirect(url_for('login'))

    user_email = session['user']
    carts = load_carts()
    carts[user_email] = []
    save_carts(carts)

    return redirect(url_for('view_cart'))


@app.route('/view_cart', methods=['GET', 'POST'])
def view_cart():
    if 'user' not in session or session.get('is_admin'):
        return redirect(url_for('login'))

    user_email = session['user']
    carts = load_carts()
    cart = carts.get(user_email, [])

    if request.method == 'POST':
        name = request.form.get('name')
        price = float(request.form.get('price'))
        quantity = int(request.form.get('quantity'))
        category = request.form.get('category')

        menu_data = load_menu()
        for category_name, items in menu_data.items():
            for item in items:
                if item['name'] == name and quantity > item['quantity']:
                    return redirect(url_for('user_menu'))  # No flash

        updated = False
        for item in cart:
            if item['name'] == name:
                item['quantity'] += quantity
                updated = True
                break

        if not updated:
            cart.append({'name': name, 'price': price, 'quantity': quantity, 'category': category})

        carts[user_email] = cart
        save_carts(carts)
        return redirect(url_for('user_menu'))

    # Validate stock and flag out-of-stock items
    menu_data = load_menu()
    for item in cart:
        item['is_sold_out'] = False
        item['current_stock'] = None
        for category_name, items in menu_data.items():
            for menu_item in items:
                if item['name'] == menu_item['name']:
                    item['current_stock'] = menu_item['quantity']
                    if item['quantity'] > menu_item['quantity']:
                        item['is_sold_out'] = True
                    break

    total = sum(item['price'] * item['quantity'] for item in cart if not item.get('is_sold_out', False))
    return render_template('view_cart.html', cart=cart, total=total)

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'user' not in session:
        return redirect(url_for('login'))

    user_email = session['user']
    carts = load_carts()
    cart_items = carts.get(user_email, [])

    if not cart_items:
        return redirect(url_for('user_menu'))

    menu_data = load_menu()

    if request.method == 'POST':
        out_of_stock_items = []
        for cart_item in cart_items:
            found = False
            for category_items in menu_data.values():
                for item in category_items:
                    if item['name'] == cart_item['name']:
                        found = True
                        if item['quantity'] < cart_item['quantity']:
                            out_of_stock_items.append(cart_item['name'])
                        break
                if found:
                    break
            if not found:
                out_of_stock_items.append(cart_item['name'])

        if out_of_stock_items:
            return redirect(url_for('view_cart'))

        # Deduct from stock
        for cart_item in cart_items:
            for category_items in menu_data.values():
                for item in category_items:
                    if item['name'] == cart_item['name']:
                        item['quantity'] -= cart_item['quantity']
                        break

        save_menu(menu_data)

        # Save the order
        orders = load_orders()
        user_orders = orders.get(user_email, [])
        last_id = load_order_counter()
        new_order_id = last_id + 1
        save_order_counter(new_order_id)

        new_order = {
            "order_id": new_order_id,
            "date": str(date.today()),  # YYYY-MM-DD
            "time": datetime.now().strftime("%H:%M:%S"),
            "items": cart_items,
            "total": sum(item['price'] * item['quantity'] for item in cart_items),
            "payment_method": request.form.get('payment_method', 'unknown'),
            "status": "In Progress",
            "assigned_to": None,  # Delivery person is not yet assigned
            "otp": None,
            "otp_attempts": 0
        }

        user_orders.append(new_order)
        orders[user_email] = user_orders
        save_orders(orders)

        carts[user_email] = []  # Clear cart after order
        save_carts(carts)

        # Automatically assign the delivery person after the order is saved
        assign_delivery_person(new_order_id)

        return redirect(url_for('user_orders'))

    total_price = sum(item['price'] * item['quantity'] for item in cart_items)
    return render_template('checkout.html', cart=cart_items, total_price=total_price)

from datetime import date

@app.route('/user_orders')
def user_orders():
    if 'user' not in session:
        return redirect(url_for('login'))

    orders_data = load_orders()
    user_email = session['user']
    user_orders_list = orders_data.get(user_email, [])

    today = str(date.today())  # 'YYYY-MM-DD' format

    # Filter only today's orders
    todays_orders = [
        order for order in user_orders_list
        if order.get('date') == today
    ]

    return render_template('user_orders.html', user=user_email, orders=todays_orders)



@app.route('/track_order/<order_id>')
def track_order(order_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    orders = load_orders()
    user_email = session['user']
    user_orders = orders.get(user_email, [])

    # Find the order by ID
    order = next((o for o in user_orders if str(o['order_id']) == str(order_id)), None)

    if not order:
        return "Order not found", 404

    # Update the status if it's 'Out for Delivery' to show delivery person's name
    if order['status'] == 'Out for Delivery' and order.get('assigned_to'):
        order['delivery_person'] = order['assigned_to']  # Make sure delivery person is visible

    return render_template('track_order.html', order=order)

import smtplib
from email.mime.text import MIMEText

def send_otp_email(user_email, otp):
    sender_email = "harsha2310653@ssn.edu.in"  # Your email
    sender_password = "ojzl xmpy ryda lsas"    # App password (better: use environment variable)

    receiver_email = user_email  # ✅ Send to actual user

    subject = "Your Delivery OTP"
    body = f"Your OTP for your order is: {otp}"

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)


@app.route('/send_otp/<int:order_id>', methods=['POST'])
def send_otp(order_id):
    if 'user' not in session or not session.get('is_delivery'):
        return redirect(url_for('login'))

    delivery_email = session['user']
    orders = load_orders()

    for user_email, user_orders in orders.items():
        for order in user_orders:
            if order['order_id'] == order_id and order['assigned_to'] == delivery_email:
                otp = random.randint(1000, 9999)
                order['otp'] = otp
                order['otp_attempts'] = 0
                save_orders(orders)
                otp_storage[order_id] = {'otp': str(otp), 'attempts': 0}

                send_otp_email(user_email, otp)
                flash("OTP sent to user.", "success")
                return redirect(url_for('delivery_orders'))

    flash("Failed to send OTP.", "error")
    return redirect(url_for('delivery_orders'))

@app.route('/verify_otp/<int:order_id>', methods=['POST'])
def verify_otp(order_id):
    entered_otp = request.form.get('entered_otp', '').strip()
    if not entered_otp:
        flash("OTP is required.", "error")
        return redirect(url_for('delivery_dashboard'))

    data = otp_storage.get(order_id)

    if not data:
        flash("OTP expired or not generated.", "error")
        return redirect(url_for('delivery_dashboard'))

    if data['attempts'] >= 3:
        update_order_status(order_id, 'Cancelled')
        del otp_storage[order_id]
        flash("Maximum attempts reached. Order Cancelled.", "error")
        return redirect(url_for('delivery_dashboard'))

    if entered_otp == data['otp']:
        update_order_status(order_id, 'Delivered')

        orders = load_orders()
        delivery_person_freed = None

        # ✅ Mark delivery person as free
        for user_orders in orders.values():
            for order in user_orders:
                if order.get('order_id') == order_id:
                    delivery_person = order.get('delivery_person')
                    if delivery_person:
                        status_data = load_delivery_status()
                        status_data[delivery_person] = 'free'
                        save_delivery_status(status_data)
                        delivery_person_freed = delivery_person
                        break

        del otp_storage[order_id]
        flash("OTP verified. Order marked as Delivered.", "success")

        # ✅ Reassign freed delivery person to next available order
        if delivery_person_freed:
            # Reload latest orders and delivery status
            orders = load_orders()
            status_data = load_delivery_status()

            for user_orders in orders.values():
                for order in user_orders:
                    if order['status'] == 'In Progress' and not order.get('delivery_person'):
                        # Check if the freed person is still free
                        if status_data.get(delivery_person_freed) == 'free':
                            # Assign manually (simulate your assign_delivery_person function)
                            order['delivery_person'] = delivery_person_freed
                            status_data[delivery_person_freed] = 'busy'
                            save_orders(orders)
                            save_delivery_status(status_data)
                            flash(f"Order {order['order_id']} assigned to {delivery_person_freed}.", "info")
                            break

    else:
        otp_storage[order_id]['attempts'] += 1
        flash("Incorrect OTP. Try again.", "error")

    return redirect(url_for('delivery_dashboard'))



def update_order_status(order_id, status):
    orders = load_orders()
    for user_email, user_orders in orders.items():
        for order in user_orders:
            if order.get('order_id') == order_id:
                order['status'] = status
                break
    save_orders(orders)

def get_free_delivery_person():
    assigned = []
    orders = load_orders()
    for user_orders in orders.values():
        for order in user_orders:
            if order.get('assigned_to'):
                assigned.append(order['assigned_to'])

    # load users.json and find delivery users not already assigned
    with open(USERS_FILE, 'r') as f:
        users = json.load(f)
    free_delivery = [email for email, info in users.items()
                     if info.get('role') == 'delivery' and email not in assigned]
    return free_delivery

@app.route('/assign_delivery/<int:order_id>')
def assign_delivery(order_id):
    if not session.get('is_admin'):
        return redirect(url_for('login'))

    assigned = assign_delivery_person(order_id)
    if assigned:
        flash(f"Order {order_id} assigned to {assigned}", "success")
    else:
        flash("No available delivery person.", "error")
    return redirect(url_for('admin_dashboard'))

def assign_delivery_person(order_id):
    delivery_status = load_delivery_status()
    orders = load_orders()
    assigned_person = None

    for user_email, user_orders in orders.items():
        for order in user_orders:
            if (
                order.get('order_id') == order_id 
                and order['status'] == 'In Progress'
                and not order.get('delivery_person')  # <== Check if unassigned
            ):
                for delivery_email, status in delivery_status.items():
                    if status == 'free':
                        order['delivery_person'] = delivery_email
                        order['assigned_to'] = delivery_email
                        order['status'] = 'Out for Delivery'
                        delivery_status[delivery_email] = 'busy'
                        assigned_person = delivery_email
                        break

    if assigned_person:
        save_orders(orders)
        save_delivery_status(delivery_status)
        return assigned_person
    return None


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)

