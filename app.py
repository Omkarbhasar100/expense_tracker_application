from flask import Flask, request, redirect, url_for, render_template, session, flash
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a strong secret key

# Database connection function
def create_connection():
    try:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="manager",
            database="classwork_db"
        )
    except Error as e:
        print(f"Error: {e}")
        return None

# Initialize the database and create tables
def init_db():
    db = create_connection()
    if db is not None:
        cursor = db.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY, 
            username VARCHAR(255) UNIQUE, 
            password VARCHAR(255))''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS expenses (
            id INT AUTO_INCREMENT PRIMARY KEY, 
            user_id INT, 
            category VARCHAR(255), 
            amount FLOAT, 
            comment TEXT, 
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE)''')
        db.commit()
        cursor.close()
        db.close()

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = create_connection()

        if db is not None:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                flash("User already exists. Please choose a different username.")
                return redirect(url_for('signup'))

            hashed_password = generate_password_hash(password)
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_password))
            db.commit()
            flash("Registration successful! You can now log in.")
            return redirect(url_for('home'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = create_connection()

        if db is not None:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            if user and check_password_hash(user[2], password):  # user[2] is the password
                session['user_id'] = user[0]  # Store user ID in session
                flash("Login successful!")
                return redirect(url_for('dashboard'))
            else:
                flash("Invalid username or password.")

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('home'))

    user_id = session['user_id']
    db = create_connection()
    expenses = []

    if db is not None:
        cursor = db.cursor()
        cursor.execute(
            "SELECT id, category, amount, created_at, updated_at, comment FROM expenses WHERE user_id = %s ORDER BY created_at DESC",
            (user_id,))
        expenses = cursor.fetchall()
        cursor.close()
        db.close()

    return render_template('dashboard.html', expenses=expenses)

@app.route('/add_expense', methods=['GET', 'POST'])
def add_expense():
    if 'user_id' not in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        category = request.form['category']
        amount = float(request.form['amount'])
        comment = request.form['comment']
        user_id = session['user_id']
        db = create_connection()

        if db is not None:
            cursor = db.cursor()
            cursor.execute("INSERT INTO expenses (user_id, category, amount, comment) VALUES (%s, %s, %s, %s)",
                           (user_id, category, amount, comment))
            db.commit()
            flash("Expense added successfully!")
            return redirect(url_for('dashboard'))

    return render_template('add_expense.html')

@app.route('/edit_expense/<int:expense_id>', methods=['GET', 'POST'])
def edit_expense(expense_id):
    if 'user_id' not in session:
        return redirect(url_for('home'))

    db = create_connection()
    expense = None

    if db is not None:
        cursor = db.cursor()
        cursor.execute("SELECT * FROM expenses WHERE id = %s", (expense_id,))
        expense = cursor.fetchone()
        cursor.close()
        db.close()

    if request.method == 'POST':
        category = request.form['category']
        amount = float(request.form['amount'])
        comment = request.form['comment']
        user_id = session['user_id']

        db = create_connection()
        if db is not None:
            cursor = db.cursor()
            cursor.execute("UPDATE expenses SET category = %s, amount = %s, comment = %s WHERE id = %s",
                           (category, amount, comment, expense_id))
            db.commit()
            flash("Expense updated successfully!")
            cursor.close()
            db.close()
            return redirect(url_for('dashboard'))

    return render_template('edit_expense.html', expense=expense)

@app.route('/delete_expense/<int:expense_id>', methods=['POST'])
def delete_expense(expense_id):
    if 'user_id' not in session:
        return redirect(url_for('home'))

    db = create_connection()

    if db is not None:
        cursor = db.cursor()
        cursor.execute("DELETE FROM expenses WHERE id = %s", (expense_id,))
        db.commit()
        flash("Expense deleted successfully!")
        cursor.close()
        db.close()

    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("You have been logged out.")
    return redirect(url_for('home'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
