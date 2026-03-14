from flask import Flask, render_template, request, redirect, url_for, session
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'secret123'

BOOKS_FILE = 'books.json'
HISTORY_FILE = 'history.json'

# Hardcoded users
users = {
    "admin": {"password": "admin123", "role": "admin"},
    "student": {"password": "student123", "role": "student"}
}

# ------------------- Utility Functions -------------------
def load_books():
    if os.path.exists(BOOKS_FILE):
        with open(BOOKS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_books(books):
    with open(BOOKS_FILE, 'w') as f:
        json.dump(books, f, indent=4)

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    return []

def save_history(history):
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=4)

# ------------------- Routes -------------------
@app.route('/')
def home():
    return redirect(url_for('login_student'))

# ------------------- Login -------------------
@app.route('/login/admin', methods=['GET', 'POST'])
def login_admin():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        if username in users and users[username]['password'] == password and users[username]['role'] == 'admin':
            session['user'] = username
            session['role'] = 'admin'
            return redirect(url_for('admin_dashboard'))
        return "Invalid admin credentials"
    return render_template('login_admin.html')

@app.route('/login/student', methods=['GET', 'POST'])
def login_student():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        if username in users and users[username]['password'] == password and users[username]['role'] == 'student':
            session['user'] = username
            session['role'] = 'student'
            return redirect(url_for('student_dashboard'))
        return "Invalid student credentials"
    return render_template('login_student.html')

# ------------------- Dashboards -------------------
@app.route('/admin')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('login_admin'))
    books = load_books()
    return render_template('admin_dashboard.html', books=books)

@app.route('/student')
def student_dashboard():
    if session.get('role') != 'student':
        return redirect(url_for('login_student'))
    books = load_books()
    return render_template('student_dashboard.html', books=books)

# ------------------- Book Management -------------------
@app.route('/add', methods=['POST'])
def add_book():
    if session.get('role') != 'admin':
        return redirect(url_for('login_admin'))
    books = load_books()
    new_book = {
        'title': request.form['title'],
        'author': request.form['author'],
        'status': 'Available'
    }
    books.append(new_book)
    save_books(books)
    return redirect(url_for('admin_dashboard'))

@app.route('/delete/<book_id>', methods=['POST'])
def delete_book(book_id):
    if session.get('role') != 'admin':
        return redirect(url_for('login_admin'))
    book_id = int(book_id)
    books = load_books()
    if 0 <= book_id < len(books):
        books.pop(book_id)
        save_books(books)
    return redirect(url_for('admin_dashboard'))

@app.route('/update/<book_id>', methods=['GET', 'POST'])
def update_book(book_id):
    if session.get('role') != 'admin':
        return redirect(url_for('login_admin'))
    book_id = int(book_id)
    books = load_books()
    if book_id < 0 or book_id >= len(books):
        return "Book not found", 404
    if request.method == 'POST':
        books[book_id]['title'] = request.form['title'].strip()
        books[book_id]['author'] = request.form['author'].strip()
        save_books(books)
        return redirect(url_for('admin_dashboard'))
    return render_template('update_book.html', book=books[book_id], book_id=book_id)

# ------------------- Issue & Return -------------------
@app.route('/issue/<book_id>', methods=['POST'])
def issue_book(book_id):
    if session.get('role') != 'admin':
        return redirect(url_for('login_admin'))
    book_id = int(book_id)
    books = load_books()
    if 'issued_to' not in books[book_id]:
        student_name = request.form['student'].strip()
        books[book_id]['issued_to'] = student_name
        books[book_id]['issued_by'] = session.get('user')
        books[book_id]['issue_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        books[book_id]['status'] = 'Issued'
        save_books(books)
        history = load_history()
        history.append({
            'title': books[book_id]['title'],
            'action': 'Issued',
            'user': student_name,
            'date': books[book_id]['issue_date']
        })
        save_history(history)
    return redirect(url_for('admin_dashboard'))

@app.route('/return/<book_id>', methods=['POST'])
def return_book(book_id):
    if session.get('role') != 'admin':
        return redirect(url_for('login_admin'))
    book_id = int(book_id)
    books = load_books()
    if 'issued_to' in books[book_id]:
        return_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        history = load_history()
        history.append({
            'title': books[book_id]['title'],
            'action': 'Returned',
            'user': books[book_id]['issued_to'],
            'date': return_date
        })
        save_history(history)
        books[book_id]['status'] = 'Available'
        books[book_id].pop('issued_to', None)
        books[book_id].pop('issue_date', None)
        books[book_id].pop('issued_by', None)
        save_books(books)
    return redirect(url_for('admin_dashboard'))

# ------------------- History Views -------------------
@app.route('/history')
def view_history():
    if session.get('role') != 'admin':
        return redirect(url_for('login_admin'))
    history = load_history()
    return render_template('history.html', history=history)

@app.route('/student/history')
def student_history():
    if session.get('role') != 'student':
        return redirect(url_for('login_student'))
    current_student = session.get('user')
    history = load_history()
    student_history = [record for record in history if record['user'] == current_student]
    return render_template('student_history.html', history=student_history)

# ------------------- Issued Books (Admin) -------------------
@app.route('/issued')
def issued_books():
    if session.get('role') != 'admin':
        return redirect(url_for('login_admin'))
    books = [b for b in load_books() if 'issued_to' in b]
    return render_template('issued_books.html', books=books)

# ------------------- Search Books -------------------
@app.route('/search', methods=['GET', 'POST'])
def search_books():
    books = load_books()
    if request.method == 'POST':
        keyword = request.form['keyword'].lower()
        books = [b for b in books if keyword in b['title'].lower() or keyword in b['author'].lower()]
    return render_template('search_results.html', books=books)

# ------------------- Logout -------------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# ------------------- Run App -------------------
if __name__ == '__main__':
    app.run(debug=True)
