from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify
import mysql.connector

# Create a Flask application instance
app = Flask(__name__)

app.secret_key = 'family'


# Function to establish a connection to the MySQL database.
def get_db_connection():
    connection = mysql.connector.connect(
        host='localhost',       # Your MySQL server address
        user='root',            # Your MySQL username
        password='Year2001#born',# Your MySQL password
        database='pottery_db'   # The database we created for our project
    )
    return connection

@app.route('/')
def index():
    # Open a connection to the database
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Fetch 12 random products from the database
    cursor.execute("SELECT * FROM products ORDER BY RAND() LIMIT 12")
    products = cursor.fetchall()
    
    # Close the cursor and connection
    cursor.close()
    conn.close()
    
    # Render the index.html template, passing the products data
    return render_template('index.html', products=products)



@app.route('/product/<int:product_id>')
def product_detail(product_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Fetch the product with the given id
    cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
    product = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    # If no product is found, return a 404 or a custom message
    if not product:
        return "Product not found", 404
    
    # Render the product detail template
    return render_template('product_detail.html', product=product)



@app.route('/products')
def all_products():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Fetch all products in random order
    cursor.execute("SELECT * FROM products ORDER BY RAND()")
    products = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('all_products.html', products=products)

@app.route('/subcategory/<int:subcategory_id>')
def subcategory_products(subcategory_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Fetch products that belong to the subcategory
    query = "SELECT * FROM products WHERE subcategory_id = %s"
    cursor.execute(query, (subcategory_id,))
    products = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('subcategory_products.html', products=products)


#--------------------------------------------------------------------------------------------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Query the user from the database
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        # For simplicity, comparing plain text (use hashing in production)
        if user and user['password'] == password:
            session['user_id'] = user['id']
            session['first_name'] = user['first_name']
            flash("Login successful!")
            return redirect(url_for('index'))
        else:
            flash("Invalid credentials, please try again.")
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.")
    return redirect(url_for('index'))

#---------------------------------------------------------------------------------------------------------------------------------------

@app.route('/add_to_cart/<int:product_id>')
def add_to_cart(product_id):
    # Check if the user is logged in
    if 'user_id' in session:
        user_id = session['user_id']
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if this product is already in the user's cart
        cursor.execute("SELECT quantity FROM cart_items WHERE user_id = %s AND product_id = %s", (user_id, product_id))
        result = cursor.fetchone()
        
        if result:
            # If it exists, increment the quantity
            cursor.execute("UPDATE cart_items SET quantity = quantity + 1 WHERE user_id = %s AND product_id = %s", (user_id, product_id))
        else:
            # Otherwise, insert it as a new row
            cursor.execute("INSERT INTO cart_items (user_id, product_id, quantity) VALUES (%s, %s, %s)", (user_id, product_id, 1))
        
        conn.commit()
        cursor.close()
        conn.close()
        flash("Product added to cart!")
    else:
        # Fallback: if the user is not logged in, use a session-based cart
        if 'cart' not in session:
            session['cart'] = {}
        cart = session['cart']
        if str(product_id) in cart:
            cart[str(product_id)] += 1
        else:
            cart[str(product_id)] = 1
        session['cart'] = cart
        flash("Product added to cart!")
    
    return redirect(url_for('index'))


@app.route('/cart')
def view_cart():
    if 'user_id' in session:
        user_id = session['user_id']
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        # Join cart_items with products to get product details along with quantity
        cursor.execute("""
            SELECT p.*, ci.quantity 
            FROM cart_items ci
            JOIN products p ON ci.product_id = p.id
            WHERE ci.user_id = %s
        """, (user_id,))
        products = cursor.fetchall()
        cursor.close()
        conn.close()
        
        total = sum(product['price'] * product['quantity'] for product in products)
        return render_template('cart.html', products=products, total=total)
    else:
        # Fallback: session-based cart
        cart = session.get('cart', {})
        product_ids = list(cart.keys())
        products = []
        if product_ids:
            placeholders = ','.join(['%s'] * len(product_ids))
            query = f"SELECT * FROM products WHERE id IN ({placeholders})"
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, product_ids)
            products = cursor.fetchall()
            cursor.close()
            conn.close()
        for product in products:
            product['quantity'] = cart.get(str(product['id']), 0)
        total = sum(product['price'] * product['quantity'] for product in products)
        return render_template('cart.html', products=products, total=total)



@app.route('/remove_from_cart/<int:product_id>')
def remove_from_cart(product_id):
    if 'user_id' in session:
        user_id = session['user_id']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cart_items WHERE user_id = %s AND product_id = %s", (user_id, product_id))
        conn.commit()
        cursor.close()
        conn.close()
    else:
        cart = session.get('cart', {})
        cart.pop(str(product_id), None)
        session['cart'] = cart
    flash("Product removed from cart.")
    return redirect(url_for('view_cart'))


#-----------------------------------------------------------------------------------------------------------------------------------


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get form data
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Basic validation: Check if passwords match
        if password != confirm_password:
            flash("Passwords do not match. Please try again.")
            return redirect(url_for('register'))
        
        # Connect to the database and check if user already exists
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            flash("A user with this email already exists!")
            cursor.close()
            conn.close()
            return redirect(url_for('register'))
        
        # Insert the new user into the users table
        # In production, hash the password before storing it!
        cursor.execute(
            "INSERT INTO users (first_name, last_name, email, password) VALUES (%s, %s, %s, %s)",
            (first_name, last_name, email, password)
        )
        conn.commit()
        cursor.close()
        conn.close()
        
        flash("Registration successful! Please log in.")
        return redirect(url_for('login'))
    
    # If GET request, display the registration form
    return render_template('register.html')

#-----------------------------------------------------------------------------------------------------------------------------------------------------------

#account
@app.route('/account')
def account():
    # Check if the user is logged in; if not, redirect to the login page.
    if 'user_id' not in session:
        flash("Please log in to view your account.")
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Retrieve user details from the users table.
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    
    # Retrieve the user's addresses from the addresses table.
    cursor.execute("SELECT * FROM addresses WHERE user_id = %s", (user_id,))
    addresses = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    # Render the account page template with the user's information and addresses.
    return render_template('account.html', user=user, addresses=addresses)

@app.route('/update_profile', methods=['POST'])
def update_profile():
    # Ensure user is logged in
    if 'user_id' not in session:
        flash("Please log in to update your profile.")
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    # Retrieve form data
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    mobile = request.form.get('mobile')
    email = request.form.get('email')
    gender = request.form.get('gender')
    
    # Connect to the database and update user information
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        UPDATE users
        SET first_name = %s, last_name = %s, mobile = %s, email = %s, gender = %s
        WHERE id = %s
    """
    cursor.execute(query, (first_name, last_name, mobile, email, gender, user_id))
    conn.commit()
    cursor.close()
    conn.close()
    
    flash("Profile updated successfully!")
    return redirect(url_for('account'))


@app.route('/add_address', methods=['POST'])
def add_address():
    if 'user_id' not in session:
        flash("Please log in to add an address.")
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    # Retrieve new address data from the form
    line1 = request.form.get('line1')
    line2 = request.form.get('line2')
    city = request.form.get('city')
    state = request.form.get('state')
    zipcode = request.form.get('zipcode')
    
    # Insert the new address into the addresses table
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        INSERT INTO addresses (user_id, line1, line2, city, state, zipcode)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    cursor.execute(query, (user_id, line1, line2, city, state, zipcode))
    conn.commit()
    cursor.close()
    conn.close()
    
    flash("Address added successfully!")
    return redirect(url_for('account'))


@app.route('/delete_address/<int:address_id>')
def delete_address(address_id):
    if 'user_id' not in session:
        flash("Please log in to delete an address.")
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "DELETE FROM addresses WHERE id = %s AND user_id = %s"
    cursor.execute(query, (address_id, user_id))
    conn.commit()
    cursor.close()
    conn.close()
    
    flash("Address deleted successfully!")
    return redirect(url_for('account'))



#search bar
#@app.route('/search_suggestions')
@app.route('/search')
def search():
    query = request.args.get('query', '')  # Get the search term
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Build a search pattern; using LIKE for partial matching
    search_pattern = f"%{query}%"
    cursor.execute(
        "SELECT * FROM products WHERE name LIKE %s OR description LIKE %s",
        (search_pattern, search_pattern)
    )
    results = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('search_results.html', products=results, query=query)





if __name__ == '__main__':
    print("Starting Flask development server...")
    app.run(debug=True)
