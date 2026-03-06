from flask import Flask, request, render_template,session,redirect, url_for,jsonify
import pandas as pd
import random
import os
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from models import db



app = Flask(__name__)

# load files===========================================================================================================
trending_products = pd.read_csv("models/trending_products.csv")
train_data = pd.read_csv("models/clean_data.csv")

# database configuration---------------------------------------
app.secret_key = "alskdjfwoeieiurlskdjfslkdjf"
# Use SQLite instead of MySQL (no server required)
import os
basedir = os.path.abspath(os.path.dirname(__file__))
instance_path = os.path.join(basedir, "instance")
# Create instance directory if it doesn't exist
os.makedirs(instance_path, exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(instance_path, "users.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Create database tables if they don't exist
with app.app_context():
    try:
        db.create_all()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Database initialization note: {e}")



# Define your model class for the 'signup' table
class Signup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)

# Define your model class for the 'signup' table
class Signin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)



# Recommendations functions============================================================================================
def keyword_based_recommendations(train_data, query, top_n=8):
    query = query.lower()

    tfidf = TfidfVectorizer(stop_words="english")
    tfidf_matrix = tfidf.fit_transform(train_data["Tags"])

    query_vec = tfidf.transform([query])
    similarity_scores = cosine_similarity(query_vec, tfidf_matrix).flatten()

    top_indices = similarity_scores.argsort()[::-1][:top_n]

    return train_data.iloc[top_indices][
        ["Name", "ReviewCount", "Brand", "ImageURL", "Rating"]
    ]

# Function to truncate product name
def truncate(text, length):
    if len(text) > length:
        return text[:length] + "..."
    else:
        return text


def content_based_recommendations(train_data, item_name, top_n=10):
    # Check if the item name exists in the training data
    if item_name not in train_data['Name'].values:
        print(f"Item '{item_name}' not found in the training data.")
        return pd.DataFrame()

    # Create a TF-IDF vectorizer for item descriptions
    tfidf_vectorizer = TfidfVectorizer(stop_words='english')

    # Apply TF-IDF vectorization to item descriptions
    tfidf_matrix_content = tfidf_vectorizer.fit_transform(train_data['Tags'])

    # Calculate cosine similarity between items based on descriptions
    cosine_similarities_content = cosine_similarity(tfidf_matrix_content, tfidf_matrix_content)

    # Find the index of the item
    item_index = train_data[train_data['Name'] == item_name].index[0]

    # Get the cosine similarity scores for the item
    similar_items = list(enumerate(cosine_similarities_content[item_index]))

    # Sort similar items by similarity score in descending order
    similar_items = sorted(similar_items, key=lambda x: x[1], reverse=True)

    # Get the top N most similar items (excluding the item itself)
    top_similar_items = similar_items[1:top_n+1]

    # Get the indices of the top similar items
    recommended_item_indices = [x[0] for x in top_similar_items]

    # Get the details of the top similar items
    recommended_items_details = train_data.iloc[recommended_item_indices][['Name', 'ReviewCount', 'Brand', 'ImageURL', 'Rating']]

    return recommended_items_details
# routes===============================================================================
# List of predefined image URLs
random_image_urls = [
    "static/img/img_1.png",
    "static/img/img_2.png",
    "static/img/img_3.png",
    "static/img/img_4.png",
    "static/img/img_5.png",
    "static/img/img_6.png",
    "static/img/img_7.png",
    "static/img/img_8.png",
]

# routes
#=============================================

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        # No dedicated login route; send user to home where sign-in modal is available
        return redirect(url_for("index") + "?redirect=dashboard")

    return render_template("dashboard.html")


@app.route("/")
def index():
    # Handle redirect parameter
    redirect_to = request.args.get('redirect')
    error = request.args.get('error')
    
    # Create a list of random image URLs for each product
    random_product_image_urls = [random.choice(random_image_urls) for _ in range(len(trending_products))]
    price = [40, 50, 60, 70, 100, 122, 106, 50, 30, 50]
    return render_template('index.html',trending_products=trending_products.head(8),truncate = truncate,
                           random_product_image_urls=random_product_image_urls,
                           random_price = random.choice(price),
                           redirect_to=redirect_to,
                           error=error)

@app.route("/main", methods=["GET", "POST"])
def main():
    content_based_rec = pd.DataFrame()
    message = None

    if request.method == "POST":
        prod = request.form.get("prod")

        content_based_rec = content_based_recommendations(
            train_data, prod, top_n=12
        )

        if content_based_rec is None or content_based_rec.empty:
            content_based_rec = keyword_based_recommendations(
                train_data, prod, top_n=12
            )
            message = "Showing recommendations based on your search"

    return render_template(
        "main.html",
        content_based_rec=content_based_rec,
        message=message
    )
@app.route("/signup", methods=['POST','GET'])
def signup():
    if request.method=='POST':
        try:
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '').strip()
            return_url = request.form.get('return_url', '/')

            # Validate inputs
            if not username or not email or not password:
                return redirect(url_for('index') + '?error=missing_fields')

            # Ensure database tables exist
            with app.app_context():
                db.create_all()

            # Check if user already exists
            try:
                existing = Signup.query.filter_by(username=username).first()
                if existing:
                    return redirect(url_for('index') + '?error=username_exists')

                # Check if email already exists
                existing_email = Signup.query.filter_by(email=email).first()
                if existing_email:
                    return redirect(url_for('index') + '?error=email_exists')

                new_signup = Signup(username=username, email=email, password=password)
                db.session.add(new_signup)
                db.session.commit()

                # Set session
                session['user_id'] = new_signup.id
                session['username'] = username
                session['email'] = email
                session.modified = True

                return redirect(return_url)
            except Exception as db_error:
                print(f"Database error during signup: {db_error}")
                db.session.rollback()
                # Try to create tables and retry once
                try:
                    db.create_all()
                    new_signup = Signup(username=username, email=email, password=password)
                    db.session.add(new_signup)
                    db.session.commit()
                    session['user_id'] = new_signup.id
                    session['username'] = username
                    session['email'] = email
                    session.modified = True
                    return redirect(return_url)
                except Exception as retry_error:
                    print(f"Retry failed: {retry_error}")
                    db.session.rollback()
                    return redirect(url_for('index') + '?error=signup_failed')
        except Exception as e:
            print(f"Signup error: {e}")
            import traceback
            traceback.print_exc()
            try:
                db.session.rollback()
            except:
                pass
            return redirect(url_for('index') + '?error=signup_failed')

    return redirect(url_for('index'))

@app.route('/signin', methods=['POST', 'GET'])
def signin():
    if request.method == 'POST':
        try:
            username = request.form.get('signinUsername', '').strip()
            password = request.form.get('signinPassword', '').strip()
            return_url = request.form.get('return_url', '/')

            if not username or not password:
                return redirect(url_for('index') + '?error=missing_fields')

            # Ensure database tables exist
            with app.app_context():
                db.create_all()

            # Validate credentials
            try:
                user = Signup.query.filter_by(username=username, password=password).first()
                if user:
                    session['user_id'] = user.id
                    session['username'] = user.username
                    session['email'] = user.email
                    session.modified = True
                    return redirect(return_url)
                else:
                    return redirect(url_for('index') + '?error=invalid_credentials')
            except Exception as db_error:
                print(f"Database error during signin: {db_error}")
                return redirect(url_for('index') + '?error=invalid_credentials')
        except Exception as e:
            print(f"Signin error: {e}")
            import traceback
            traceback.print_exc()
            return redirect(url_for('index') + '?error=invalid_credentials')

    return redirect(url_for('index'))

@app.route("/index")
def indexredirect():
    # Create a list of random image URLs for each product
    random_product_image_urls = [random.choice(random_image_urls) for _ in range(len(trending_products))]
    price = [40, 50, 60, 70, 100, 122, 106, 50, 30, 50]
    return render_template('index.html', trending_products=trending_products.head(8), truncate=truncate,
                           random_product_image_urls=random_product_image_urls,
                           random_price=random.choice(price))




DEFAULT_RECOMMENDATIONS = 12

@app.route("/reccom", methods=['POST', 'GET'])
def recommendations():
    if request.method == 'POST':
        prod = request.form.get('prod')

        # Always use default
        nbr = DEFAULT_RECOMMENDATIONS

        # Exact product-based recommendation
        content_based_rec = content_based_recommendations(
            train_data, prod, top_n=nbr
        )

        # Fallback to keyword-based
        if content_based_rec is None or content_based_rec.empty:
            content_based_rec = keyword_based_recommendations(
                train_data, prod, top_n=nbr
            )
            message = "Showing recommendations based on your search"
        else:
            message = None

        random_product_image_urls = [
            random.choice(random_image_urls)
            for _ in range(len(content_based_rec))
        ]

        price = [40, 50, 60, 70, 100, 122, 106, 50, 30, 50]

        return render_template(
            'main.html',
            content_based_rec=content_based_rec,
            truncate=truncate,
            random_product_image_urls=random_product_image_urls,
            random_price=random.choice(price),
            message=message
        )

@app.route("/profile")
def profile():
    if "user_id" not in session:
        # Redirect unauthenticated users to home with intent
        return redirect(url_for("index") + "?redirect=profile")

    return render_template("profile.html")

@app.route("/logout")
def logout():
    session.clear()
    # After logout, send user to home where they can sign in again
    return redirect(url_for("index"))


@app.route("/add_to_cart", methods=["POST"])
def add_to_cart():
    data = request.get_json()

    cart = session.get("cart")

    # 🚨 FORCE FIX
    if not isinstance(cart, dict):
        cart = {}

    pid = str(data["id"])

    if pid in cart:
        cart[pid]["quantity"] += 1
    else:
        cart[pid] = {
            "name": data["name"],
            "brand": data["brand"],
            "price": float(data["price"]),
            "image": data["image"],
            "quantity": 1
        }

    session["cart"] = cart
    session.modified = True

    return jsonify(
        cart_count=sum(item["quantity"] for item in cart.values())
    )


@app.route("/cart")
def cart():
    cart = session.get("cart")

    # 🚨 FORCE FIX AGAIN
    if not isinstance(cart, dict):
        cart = {}

    total = sum(
        item["price"] * item["quantity"]
        for item in cart.values()
    )

    return render_template("cart.html", cart=cart, total=total)

@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    # Require authentication
    if "user_id" not in session:
        return redirect(url_for("index") + "?redirect=checkout")

    cart = session.get("cart", {})

    if not cart:
        return redirect(url_for("cart"))

    total = sum(
        item["price"] * item["quantity"]
        for item in cart.values()
    )

    if request.method == "POST":
        # Collect form data
        full_name = request.form.get("full_name")
        contact = request.form.get("contact")
        email = request.form.get("email", session.get("email", ""))
        address_line = request.form.get("address_line")
        city = request.form.get("city")
        state = request.form.get("state")
        pincode = request.form.get("pincode")
        payment_method = request.form.get("payment_method")
        payment_details = {}

        if payment_method == "upi":
            payment_details["upi_id"] = request.form.get("upi_id")
        elif payment_method == "card":
            payment_details["card_number"] = request.form.get("card_number")
            payment_details["expiry"] = request.form.get("expiry")
            payment_details["cvv"] = request.form.get("cvv")

        # Generate order ID
        import uuid
        from datetime import datetime
        order_id = str(uuid.uuid4())[:8].upper()

        # Save order
        order = {
            "order_id": order_id,
            "items": cart,
            "total": total,
            "shipping": {
                "full_name": full_name,
                "contact": contact,
                "email": email,
                "address_line": address_line,
                "city": city,
                "state": state,
                "pincode": pincode
            },
            "payment_method": payment_method,
            "payment_details": payment_details,
            "date": datetime.now().strftime("%Y-%m-%d")
        }

        # Save to orders list
        orders = session.get("orders", [])
        orders.append(order)
        session["orders"] = orders
        session["last_order"] = order

        # Clear cart after purchase
        session.pop("cart", None)

        return redirect(url_for("order_success"))

    return render_template("checkout.html", cart=cart, total=total)

@app.route("/order-success")
def order_success():
    if "user_id" not in session:
        return redirect(url_for("index"))

    order = session.get("last_order")

    if not order:
        return redirect(url_for("index"))

    return render_template("order_success.html", order=order)


@app.route("/orders")
def orders():
    if "user_id" not in session:
        return redirect(url_for("index") + "?redirect=orders")

    orders_list = session.get("orders", [])
    # Ensure orders is a list and each order has proper structure
    if not isinstance(orders_list, list):
        orders_list = []
    
    # Filter orders to ensure they have the required structure
    valid_orders = []
    for order in orders_list:
        if isinstance(order, dict) and "order_id" in order:
            # Create a safe copy of the order
            order_copy = dict(order)
            items = order.get("items", {})
            
            # Convert items dict to a list format for easier template iteration
            if isinstance(items, dict):
                items_list = []
                for pid, item_data in items.items():
                    if isinstance(item_data, dict):
                        items_list.append({
                            'pid': str(pid),
                            'name': item_data.get('name', 'Unknown Product'),
                            'brand': item_data.get('brand', ''),
                            'price': float(item_data.get('price', 0)),
                            'quantity': int(item_data.get('quantity', 1)),
                            'image': item_data.get('image', 'https://via.placeholder.com/60x60?text=Product')
                        })
                order_copy["items_list"] = items_list
                order_copy["items"] = items  # Keep original for backward compatibility
            else:
                order_copy["items_list"] = []
                order_copy["items"] = {}
            
            valid_orders.append(order_copy)
    
    # Reverse the list to show newest orders first
    valid_orders.reverse()
    
    return render_template("orders.html", orders=valid_orders)


@app.route("/remove/<pid>")
def remove_from_cart(pid):
    cart = session.get("cart", {})
    cart.pop(pid, None)
    session["cart"] = cart
    session.modified = True
    return redirect(url_for("cart"))

if __name__=='__main__':
    # Ensure database is initialized before running
    with app.app_context():
        try:
            db.create_all()
            print("✓ Database ready")
        except Exception as e:
            print(f"⚠ Database initialization warning: {e}")
    app.run(debug=True)