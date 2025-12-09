from flask import Flask, render_template, request, redirect, session, url_for, flash
import mysql.connector, os
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Ensure uploads folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ---------- Database Connection ----------
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="virtual_internship"
    )

# ---------- Home ----------
@app.route('/')
def index():
    return render_template('index.html')

# ---------- About ----------
@app.route('/about')
def about():
    return render_template('about.html')

# ---------- Contact ----------
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        flash("Your message has been received! Thank you for reaching out.", "success")
        return redirect(url_for('contact'))
    return render_template('contact.html')

# ---------- Register ----------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        education = request.form.get('education')
        skills = request.form.get('skills')

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO registration (name, email, password, education, skills, joining_date)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (name, email, password, education, skills, datetime.now().strftime("%Y-%m-%d")))
        conn.commit()
        cursor.close()
        conn.close()

        flash("Registration successful! Please login.", "success")
        return redirect(url_for('login'))
    return render_template('register.html')

# ---------- Login ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Admin Login
        if email == "admin@gmail.com" and password == "admin123":
            session['role'] = 'admin'
            session['user_id'] = 0
            session['name'] = "Admin"
            session['email'] = email
            flash("Welcome Admin!", "success")
            return redirect(url_for('admin_dashboard'))

        # Intern Login
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM registration WHERE email=%s AND password=%s", (email, password))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            session['role'] = 'intern'
            session['user_id'] = user['id']
            session['name'] = user['name']
            session['email'] = user['email']
            flash(f"Welcome {user['name']}!", "success")
            return redirect(url_for('intern_dashboard'))
        else:
            flash("Invalid email or password.", "danger")

    return render_template('login.html')

# ---------- Admin Dashboard ----------
@app.route('/admin_dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    return render_template('admin_dashboard.html')

# ---------- Add Internship ----------
@app.route('/add_internship', methods=['GET', 'POST'])
def add_internship():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        duration = request.form['duration']
        stipend = request.form['stipend']
        posted_by = request.form['posted_by']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO internships (title, description, duration, stipend, posted_by)
            VALUES (%s, %s, %s, %s, %s)
        """, (title, description, duration, stipend, posted_by))
        conn.commit()
        cursor.close()
        conn.close()

        flash("✅ Internship added successfully!", "success")
        return redirect(url_for('add_internship'))

    return render_template('add_internship.html')

# ---------- Intern Dashboard ----------
@app.route('/intern_dashboard')
def intern_dashboard():
    if session.get('role') != 'intern':
        return redirect(url_for('login'))

    intern_id = session.get('user_id')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM internships")
    internships = cursor.fetchall()

    cursor.execute("""
        SELECT a.application_id, a.status, i.title, i.description, a.internship_id
        FROM applications a
        JOIN internships i ON a.internship_id = i.id
        WHERE a.intern_id = %s
    """, (intern_id,))
    applications = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template('intern_dashboard.html', internships=internships, applications=applications)

# ---------- Apply Internship ----------
@app.route('/apply_internship', methods=['POST'])
def apply_internship():
    if session.get('role') != 'intern':
        flash("Please log in first!", "danger")
        return redirect(url_for('login'))

    internship_id = request.form.get('internship_id')
    intern_id = session.get('user_id')
    file = request.files.get('resume')

    filename = None
    if file and file.filename != '':
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT * FROM applications
        WHERE intern_id = %s AND internship_id = %s
    """, (intern_id, internship_id))
    existing = cursor.fetchone()

    if existing:
        flash("You have already applied for this internship.", "warning")
    else:
        cursor.execute("""
            INSERT INTO applications (intern_id, internship_id, status, image)
            VALUES (%s, %s, %s, %s)
        """, (intern_id, internship_id, 'Pending', filename))

        conn.commit()
        flash("Application submitted successfully!", "success")

    cursor.close()
    conn.close()
    return redirect(url_for('intern_dashboard'))

# ---------- Upload Photo ----------
@app.route('/update_status/<int:id>', methods=['POST'])
def update_status(id):
    status = request.form['status']
    file = request.files['file']
    
    filename = None
    if file and file.filename != '':
        filename = file.filename
        file.save(os.path.join('static/uploads', filename))  # folder must exist

    cursor = mydb.cursor()
    query = "UPDATE applied_internships SET status=%s, document=%s WHERE id=%s"
    cursor.execute(query, (status, filename, id))
    mydb.commit()
    cursor.close()

    flash("Internship status updated successfully!", "success")
    return redirect('/admin_dashboard')


# ---------- View All Applications (Admin) ----------
@app.route('/view_applications')
def view_applications():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT 
            a.application_id, 
            r.name, 
            i.title, 
            a.status,
            COALESCE(t.image, 'no_image.jpg') AS image
        FROM applications a
        JOIN registration r ON a.intern_id = r.id
        JOIN internships i ON a.internship_id = i.id
        LEFT JOIN (
            SELECT assigned_to, MAX(image) AS image
            FROM tasks
            GROUP BY assigned_to
        ) t ON t.assigned_to = a.intern_id
    """)
    applications = cursor.fetchall()
    conn.close()
    return render_template('view_applications.html', applications=applications)

# ---------- Approve / Reject ----------
@app.route('/accept_application/<int:app_id>')
def accept_application(app_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE applications SET status = 'Accepted' WHERE application_id = %s", (app_id,))
    conn.commit()
    conn.close()
    flash("Application Accepted!", "success")
    return redirect(url_for('view_applications'))

@app.route('/delete_application/<int:app_id>')
def delete_application(app_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM applications WHERE application_id = %s", (app_id,))
    conn.commit()
    conn.close()
    flash("Application Deleted!", "info")
    return redirect(url_for('view_applications'))

# ---------- Submit Work ----------
@app.route('/submit_work/<int:app_id>', methods=['POST'])
def submit_work(app_id):
    if session.get('role') != 'intern':
        return redirect(url_for('login'))

    image = request.files.get('image')
    if image and image.filename != '':
        filename = secure_filename(image.filename)
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE applications SET status=%s WHERE application_id=%s", ('Submitted', app_id))
        cursor.execute("""
            INSERT INTO tasks (title, description, assigned_to, image, due_date)
            VALUES (%s, %s, %s, %s, %s)
        """, ('Submitted Work', 'Intern submitted the work.', session['user_id'], filename, datetime.now()))
        conn.commit()
        cursor.close()
        conn.close()
        flash("Work submitted successfully!", "success")
    else:
        flash("Please upload a valid image.", "danger")

    return redirect(url_for('intern_dashboard'))

# ---------- View Tasks ----------
@app.route('/view_tasks')
def view_tasks():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM tasks")
    tasks = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('view_tasks.html', tasks=tasks)

# ---------- Add Task ----------
@app.route('/add_task', methods=['GET', 'POST'])
def add_task():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        assigned_to = request.form['assigned_to']
        due_date = request.form['due_date']
        status = 'Pending'

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tasks (title, description, assigned_to, status, due_date)
            VALUES (%s, %s, %s, %s, %s)
        """, (title, description, assigned_to, status, due_date))
        conn.commit()
        cursor.close()
        conn.close()
        flash('Task added successfully!', 'success')
        return redirect(url_for('view_tasks'))

    return render_template('add_task.html')

# ---------- Logout ----------
@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for('login'))

# ---------- Run Flask ----------
if __name__ == '__main__':
    app.run(debug=True, port=5070)
