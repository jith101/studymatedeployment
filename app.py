from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_from_directory
from flask_mysqldb import MySQL
import random
from flask_mail import Mail, Message
import os
import random
import string
from datetime import datetime
import stripe
from werkzeug.utils import secure_filename
import numpy as np
import gensim
from sklearn.neighbors import KNeighborsClassifier
from transformers import pipeline
from MySQLdb.cursors import DictCursor

import MySQLdb.cursors

app = Flask(__name__)
app.secret_key = "your-secret-key"

app.config['MYSQL_HOST'] = "qm5vp.h.filess.io"
app.config['MYSQL_USER'] = "s9project_southernup"
app.config['MYSQL_PASSWORD'] = "35d2ab552dd96afe99fe3fcd1a9990c5bf632763"
app.config['MYSQL_DB'] = "s9project_southernup"
app.config['MYSQL_PORT'] = 3307

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

mysql = MySQL(app)

# Configure Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'studymateproject@gmail.com'
app.config['MAIL_PASSWORD'] = 'qjxp aypx jkub oahs'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
mail = Mail(app)
otps = {}


@app.route('/')
def home():
    if 'email' in session:
        return render_template('home.html', email=session['email'])
    else:
        return render_template('home.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM tbl_user WHERE email = %s", [email])
        user = cur.fetchone()
        cur.close()

        # Assuming password is stored in the fourth column
        if user is not None and password == user[3]:
            session['name'] = user[1]
            session['uid'] = user[0]
            session['email'] = user[2]

            if email == "admin@gmail.com" and password == "Admin@2002":
                flash("Login successful! You will be redirected shortly.", "success")
                return redirect(url_for('admin_dashboard_acceptTeacher'))
            elif user[4] == 3:  # Assuming user_type is stored in the fifth column
                flash("Login successful! You will be redirected shortly.", "success")
                return redirect(url_for('student_assigned_course'))
            elif user[4] == 2:
                # Fetch the new_date value from tbl_user
                cur = mysql.connection.cursor()
                cur.execute("SELECT new_date FROM tbl_user WHERE uid = %s", [
                            session['uid']])
                new_data = cur.fetchone()[0]

                # Fetch the tid from the teacher table using the uid from session
                cur.execute("SELECT tid FROM teacher WHERE uid = %s", [
                            session['uid']])
                tid = cur.fetchone()[0]

                # Store tid in session
                session['tid'] = tid

                cur.close()

                if new_data == 1:
                    flash(
                        "You need to update your password before proceeding.", "warning")
                    return redirect(url_for('update_password_teacher'))
                else:
                    flash(
                        "Login successful! You will be redirected shortly.", "success")
                    return redirect(url_for('teacher_dashboard_show'))
        # return redirect(url_for('teacher_dashboard_show'))
            else:
                flash("Invalid user type.", "danger")
                return render_template('login.html', success=False)
        else:
            flash("Invalid Credentials. Please try again.", "danger")
            return render_template('login.html', success=False)
    return render_template('login.html', success=False)


@app.route('/admin_dashboard_acceptTeacher')
def admin_dashboard_acceptTeacher():
    return render_template('admin_dashboard_acceptTeacher.html')


@app.route('/student_dashboard')
def student_dashboard():
    if 'uid' not in session:
        # If not logged in, redirect to the login page
        return redirect(url_for('login'))
    return render_template('courses.html')


# ------------------------------------------------------------------------- code
def validate_password(password):
    import re
    # Check for length, uppercase, lowercase, digit, and special character
    return (len(password) >= 8 and
            re.search(r'[A-Z]', password) and
            re.search(r'[a-z]', password) and
            re.search(r'\d', password) and
            re.search(r'[@$!%*?&]', password))


@app.route('/update_password_teacher', methods=['GET', 'POST'])
def update_password_teacher():
    if 'uid' not in session:
        flash("You need to log in first.", "danger")
        return redirect(url_for('login'))

    if request.method == 'POST':
        new_password = request.form['new_password']
        uid = session.get('uid')

        # Validate the new password
        if not validate_password(new_password):
            flash("Password does not meet the required criteria.", "danger")
            return render_template('update_password_teacher.html')

        # Update the password in the database
        cur = mysql.connection.cursor()
        cur.execute(
            "UPDATE tbl_user SET password = %s, new_date = 0 WHERE uid = %s", (new_password, uid))
        mysql.connection.commit()
        cur.close()

        flash("Password updated successfully.", "success")
        return redirect(url_for('teacher_dashboard_show'))

    return render_template('update_password_teacher.html')

# @app.route('/teacher_dashboard_show')
# def teacher_dashboard_show():

#     return render_template('teacher_dashboard_show.html')


@app.route('/teacher_dashboard_show')
def teacher_dashboard_show():
    # Assuming session['uid'] contains the tid (teacher id)
    tid = session.get('uid')
    if not tid:
        return "User not logged in"

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Fetch course_id(s) for the teacher
    cursor.execute(
        "SELECT course_id FROM teacher_course WHERE tid = %s", (tid,))
    courses = cursor.fetchall()

    course_info_list = []

    # Fetch course information using course_id
    for course in courses:
        cursor.execute("""
            SELECT name, cours_desc, start_date, end_date 
            FROM course_list 
            WHERE course_id = %s AND hide = 0
        """, (course['course_id'],))
        course_info = cursor.fetchone()
        if course_info:
            course_info_list.append(course_info)

    cursor.close()

    # Pass the course_info_list to the template for rendering
    return render_template('teacher_dashboard_show.html', courses=course_info_list)


# @app.route('/register', methods=['GET', 'POST'])
# def register():
#     if request.method == "POST":
#         name = request.form['name']
#         email = request.form['email']
#         password = request.form['password']
#         cur = mysql.connection.cursor()
#         cur.execute("SELECT email FROM tbl_user WHERE email = %s", [email])
#         existing_user = cur.fetchone()
#         if existing_user:
#             cur.close()
#             return render_template('register.html', error="Email already registered. Please use a different email.")

#         cur.execute("INSERT INTO tbl_user (email, password,name) VALUES (%s, %s,%s)", (email, password,name))
#         mysql.connection.commit()
#         cur.close()
#         session['email'] = email
#         return redirect(url_for('login'))
#     return render_template('register.html')
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute("SELECT email FROM tbl_user WHERE email = %s", [email])
        existing_user = cur.fetchone()
        if existing_user:
            cur.close()
            return render_template('register.html', error="Email already registered. Please use a different email.")

        cur.execute("INSERT INTO tbl_user (email, password, name, user_type) VALUES (%s, %s, %s, %s)",
                    (email, password, name, 3))

        mysql.connection.commit()
        cur.close()
        # session['email'] = email
        # session['name'] = name
        flash("User successfully registered. Please Login!!!.")
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/logout')
def logout():
    session.pop('email', None)
    session.pop('name', None)
    session.pop('uid', None)
    return redirect(url_for('home'))


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        cur = mysql.connection.cursor()
        cur.execute("SELECT email FROM tbl_user WHERE email = %s", [email])
        user = cur.fetchone()
        cur.close()
        if user is not None:
            otp = random.randint(100000, 999999)
            otps[email] = otp
            msg = Message('Your OTP for password reset',
                          sender='studymateproject@gmail.com', recipients=[email])
            msg.body = f'Your OTP is {otp}.'
            mail.send(msg)
            flash('OTP sent to your email address.', 'info')
            return redirect(url_for('reset_password', email=email))
        else:
            flash('Email not found. Please check and try again.', 'danger')
    return render_template('forgot_password.html')


@app.route('/reset_password/<email>', methods=['GET', 'POST'])
def reset_password(email):
    if request.method == 'POST':
        entered_otp = request.form['otp']
        new_password = request.form['new_password']
        if otps.get(email) == int(entered_otp):
            cur = mysql.connection.cursor()
            cur.execute(
                "UPDATE tbl_user SET password = %s WHERE email = %s", (new_password, email))
            mysql.connection.commit()
            cur.close()
            del otps[email]
            flash('Password reset successful.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Invalid OTP. Please try again.', 'danger')
    return render_template('reset_password.html', email=email)

# admin create course

# @app.route('/create_course', methods=['GET', 'POST'])
# def create_course():
#     if request.method == 'POST':
#         name = request.form['name']
#         cours_desc = request.form['cours_desc']
#         cost = request.form['cost']
#         start_date = request.form['start_date']
#         end_date = request.form['end_date']

#         cursor = mysql.connection.cursor()
#         cursor.execute(''' INSERT INTO course_list (name, cours_desc, cost, start_date, end_date)
#                           VALUES (%s, %s, %s, %s, %s) ''',
#                        (name, cours_desc, cost, start_date, end_date))
#         mysql.connection.commit()
#         cursor.close()

#         flash('Course created successfully!', 'success')
#         return redirect(url_for('create_course'))

#     return render_template('create_course.html')

# ----------------------------------------------------------------- CODE FOR NEW TEACHER APPLY - START ( teacher_reg.html )
# Function to generate a random six-digit password


def generate_password():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


@app.route('/teacher_reg', methods=['GET', 'POST'])
def register_teacher():
    if request.method == 'POST':
        # Get form data
        name = request.form['name']
        email = request.form['email']
        desc = request.form['desc']
        exp = request.form['exp']
        subject = request.form['subject']
        image = request.files['image']
        resume = request.files['resume']

        # Generate random password
        password = generate_password()

        # Save files
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
        resume_path = os.path.join(
            app.config['UPLOAD_FOLDER'], resume.filename)
        image.save(image_path)
        resume.save(resume_path)

        cursor = mysql.connection.cursor()

        # Insert into user table
        cursor.execute('''INSERT INTO tbl_user (name, email, password, user_type, new_date)
                          VALUES (%s, %s, %s, %s, %s)''',
                       (name, email, password, 2, 1))
        mysql.connection.commit()

        # Get the uid of the newly inserted user
        cursor.execute('SELECT uid FROM tbl_user WHERE email = %s', (email,))
        user = cursor.fetchone()
        uid = user[0]

        # Insert into teacher table
        cursor.execute('''INSERT INTO teacher (uid, des, exp, subject, image_path, resume_path, flag)
                          VALUES (%s, %s, %s, %s, %s, %s, %s)''',
                       (uid, desc, exp, subject, image_path, resume_path, 0))
        mysql.connection.commit()

        cursor.close()

        flash('Registration successful and admin has to accept the request.', 'success')
        return redirect(url_for('register_teacher'))

    return render_template('teacher_reg.html')


@app.route('/check_availability', methods=['POST'])
def check_availability():
    field = request.form['field']
    value = request.form['value']
    cursor = mysql.connection.cursor()
    cursor.execute(
        f'SELECT COUNT(*) FROM tbl_user WHERE {field} = %s', (value,))
    count = cursor.fetchone()[0]
    cursor.close()

    if count > 0:
        return jsonify({'available': False, 'message': f'{field.capitalize()} already exists.'})
    else:
        return jsonify({'available': True})
# ----------------------------------------------------------------- CODE FOR NEW TEACHER APPLY - END


@app.route('/search.html')
def search_page():
    return render_template('search.html')


@app.route('/search_teachers', methods=['GET'])
def search_teachers():
    email = request.args.get('email')
    if email:
        cur = mysql.connection.cursor()
        # Search in the user table first
        cur.execute("SELECT uid, name FROM tbl_user WHERE email = %s", (email,))
        user = cur.fetchone()
        if user:
            uid, name = user
            # Now search in the teacher table using the uid
            cur.execute("SELECT flag FROM teacher WHERE uid = %s", (uid,))
            teacher = cur.fetchone()
            if teacher:
                status = teacher[0]
                if status == 0:
                    status_message = "pending"
                elif status == 1:
                    status_message = "admin accepted you, search your email for temporary password"
                else:
                    status_message = "unknown status"
                cur.close()
                return jsonify(teachers=[{"name": name, "status": status_message}])
            else:
                cur.close()
                return jsonify(teachers=[{"name": name, "status": "not found in teacher table"}])
        else:
            cur.close()
            return jsonify(teachers=[{"name": "N/A", "status": "email not found in teacher database , please apply again"}])
    return jsonify(teachers=[])


# ------------------------------------------------------------- code for admin_dashboard_acceptteacher - start
@app.route('/get_teacher_applications')
def get_teacher_applications():
    cursor = mysql.connection.cursor()
    query = """
    SELECT 
        t.uid AS teacher_uid, t.des, t.exp, t.image_path, t.resume_path, 
        u.name AS user_name, u.email AS user_email 
    FROM 
        teacher t 
    JOIN 
        tbl_user u 
    ON 
        t.uid = u.uid 
    WHERE 
        t.flag = 0
    """
    cursor.execute(query)
    applications = cursor.fetchall()
    cursor.close()
    return jsonify(applications)


@app.route('/approve_teacher', methods=['POST'])
def approve_teacher():
    teacher_uid = request.form['teacher_uid']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    cursor.execute(
        "UPDATE teacher SET flag = 1 WHERE uid = %s", (teacher_uid,))
    cursor.execute(
        "SELECT name, email, password FROM tbl_user WHERE uid = %s", (teacher_uid,))
    user = cursor.fetchone()

    mysql.connection.commit()
    cursor.close()

    # Send approval email
    msg = Message('Welcome!', sender='studymateproject@gmail.com',
                  recipients=[user['email']])
    msg.html = f"""
    <div style="border: 1px solid #ddd; padding: 20px; font-family: Arial, sans-serif;">
        <h2>Welcome, {user['name']}!</h2>
        <p>Your account has been approved. Here are your login details:</p>
        <p><strong>Password:</strong> {user['password']}</p>
        <p>Please change your password after logging in for the first time.</p>
    </div>
    """
    mail.send(msg)

    return '', 200


@app.route('/deny_teacher', methods=['POST'])
def deny_teacher():
    teacher_uid = request.form['teacher_uid']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    cursor.execute(
        "UPDATE teacher SET flag = -1 WHERE uid = %s", (teacher_uid,))
    cursor.execute("SELECT email FROM tbl_user WHERE uid = %s", (teacher_uid,))
    teacher = cursor.fetchone()

    mysql.connection.commit()
    cursor.close()

    # Send denial email
    msg = Message('Application Denied',
                  sender='studymateproject@gmail.com', recipients=[teacher['email']])
    msg.html = """
    <div style="border: 1px solid #ddd; padding: 20px; font-family: Arial, sans-serif;">
        <h2>Application Denied</h2>
        <p>We regret to inform you that your application has been denied. Thank you for your interest.</p>
    </div>
    """
    mail.send(msg)

    return '', 200
# ------------------------------------------------------------- code for admin_dashboard_acceptteacher - end

# ------------------------------------------------------------- code for admin_create_course - start ( admin_create_course.html )
# def get_db_connection():
#     connection = MySQLdb.connect(
#         host=app.config['MYSQL_HOST'],
#         user=app.config['MYSQL_USER'],
#         passwd=app.config['MYSQL_PASSWORD'],
#         db=app.config['MYSQL_DB'],
#         cursorclass=MySQLdb.cursors.DictCursor
#     )
#     return connection


@app.route('/admin_create_course', methods=['GET', 'POST'])
def create_course():
    if request.method == 'POST':
        course_type = request.form['course_type']
        teachers = request.form.getlist('teachers')
        desc = request.form['desc']
        price = request.form['price']
        start_date = request.form['start_date']
        end_date = request.form['end_date']

        try:
            # Save course to database
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

            # Insert course
            cursor.execute('INSERT INTO course_list (name, cours_desc, cost, start_Date, end_date) VALUES (%s, %s, %s, %s, %s)',
                           (course_type, desc, price, start_date, end_date))
            course_id = cursor.lastrowid

            # Assign teachers to course
            for teacher_id in teachers:
                cursor.execute(
                    'INSERT INTO teacher_course (tid, course_id) VALUES (%s, %s)', (teacher_id, course_id))

            mysql.connection.commit()
            cursor.close()

            flash('Course created successfully!', 'success')
        except MySQLdb.Error as e:
            print("Error creating course:", e)
            flash('An error occurred while creating the course.', 'error')

        # return redirect(url_for('create_course'))

    return render_template('admin_create_course.html')


@app.route('/get_teachers', methods=['GET'])
def get_teachers():
    course_type = request.args.get('course_type')

    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # Adjust the query based on the course type
        if course_type == 'JEE / KEAM':
            subjects = ('Physics', 'Chemistry', 'Maths')
        elif course_type == 'NEET':
            subjects = ('Physics', 'Chemistry', 'Biology')
        else:
            subjects = ()  # If no course type matches, return no subjects

        # Fetch teachers based on course type with a join between tbl_user and teacher tables
        if subjects:
            query = '''
            SELECT u.uid AS id, u.name, t.subject 
            FROM tbl_user u
            JOIN teacher t ON u.uid = t.uid
            WHERE t.subject IN %s
            '''
            cursor.execute(query, (subjects,))
            teachers = cursor.fetchall()
        else:
            teachers = []
    except MySQLdb.Error as e:
        print("Error fetching teachers:", e)
        teachers = []
    finally:
        cursor.close()

    return jsonify({'teachers': teachers})


@app.route('/courses')
def courses():

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM course_list where hide = 0")
    courses = cursor.fetchall()

    cursor.close()
    return render_template('courses.html', courses=courses)


@app.route('/course/<int:course_id>')
def course_detail(course_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(
        "SELECT * FROM course_list WHERE course_id = %s", (course_id,))
    print(course_id)
    course = cursor.fetchone()
    cursor.close()
    return jsonify(course)


# ---------------------------------------------------------------------------------
@app.route('/course_list')
def course_list():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM course_list")
    courses = cursor.fetchall()
    cursor.close()
    return render_template('course_list.html', courses=courses)


@app.route('/toggle_course_visibility', methods=['POST'])
def toggle_course_visibility():
    course_id = request.json.get('course_id')
    hide_status = request.json.get('hide_status')
    new_status = 1 if hide_status == 0 else 0

    cursor = mysql.connection.cursor()
    cursor.execute(
        "UPDATE course_list SET hide = %s WHERE course_id = %s", (new_status, course_id))
    mysql.connection.commit()
    cursor.close()

    return jsonify({"success": True, "new_status": new_status})


# ----------------------------------------------  teacher_profile_update -start
# Flask route to render the update form
@app.route('/update_teacher', methods=['GET', 'POST'])
def update_teacher():
    if 'uid' not in session:
        return redirect(url_for('login'))

    uid = session['uid']

    # Fetch existing data
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('''
        SELECT u.name, t.des, t.exp, t.subject 
        FROM tbl_user u 
        JOIN teacher t ON u.uid = t.uid 
        WHERE u.uid = %s
    ''', (uid,))
    user = cursor.fetchone()

    if request.method == 'POST':
        name = request.form['name']
        des = request.form['des']
        exp = request.form['exp']
        subject = request.form['subject']
        password = request.form['password']

        # Update the user and teacher records
        cursor.execute('''
            UPDATE tbl_user u 
            JOIN teacher t ON u.uid = t.uid 
            SET u.password = %s, u.name = %s, t.des = %s, t.exp = %s, t.subject = %s 
            WHERE u.uid = %s
        ''', (password, name, des, exp, subject, uid))
        mysql.connection.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('teacher_dashboard_show'))

    return render_template('update_teacher.html', user=user)


@app.route('/check_email', methods=['POST'])
def check_email():
    email = request.form['email']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM tbl_user WHERE email = %s', (email,))
    user = cursor.fetchone()
    if user:
        return 'exists'
    return 'not_exists'


@app.route('/assigned_courses', methods=['GET'])
def assigned_courses():
    if 'uid' not in session:
        return redirect(url_for('login'))

    uid = session['uid']

    # Fetch the teacher's tid based on uid
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT tid FROM teacher WHERE uid = %s', (uid,))
    teacher = cursor.fetchone()

    if teacher:
        tid = teacher['tid']
        print(tid)
        # Fetch the assigned courses for the teacher
        cursor.execute('''
            SELECT cl.name, cl.start_Date, cl.end_date 
            FROM teacher_course tc
            JOIN course_list cl ON tc.course_id = cl.course_id
            WHERE tc.tid = %s
        ''', (uid,))
        courses = cursor.fetchall()

        return render_template('assigned_courses.html', courses=courses)
    else:
        flash('No courses assigned to this teacher.', 'warning')
        return redirect(url_for('teacher_dashboard_show'))


# Stripe keys
stripe.api_key = "sk_test_51PqTo5SJCzDLwdFn5i7x1HagUMlq9niP1pDxspf8xZK1C0Cg8GYXg2Mo0hv0wf6qTdrNCRc2o1Qo5648PSynKORc00o8jR17jz"


@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    data = request.json
    try:
        # Check if course_id is provided
        course_id = data.get('courseId')
        if not course_id:
            raise ValueError("courseId is missing from the request payload.")

        # Now use the course_id to create the checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'inr',
                    'product_data': {
                        'name': data['courseName'],
                    },
                    'unit_amount': data['amount'],
                },
                'quantity': 1,
            }],
            mode='payment',
            # Store course_id in session metadata
            metadata={'course_id': course_id},
            shipping_address_collection={
                'allowed_countries': ['IN']
            },
            success_url=request.host_url +
            'payment/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.host_url + 'payment/cancel',
        )
        return jsonify({'id': checkout_session.id})
    except Exception as e:
        return jsonify(error=str(e)), 403

# Helper function to insert payment details


def insert_payment_details(payment_id, course_id, uid, purchase_amt):
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        query = '''INSERT INTO purchase_detail (payment_id, course_id, uid, purchase_amt, date)
                   VALUES (%s, %s, %s, %s, CURDATE())'''
        cursor.execute(query, (payment_id, course_id, uid, purchase_amt))
        mysql.connection.commit()  # Commit the transaction to save the changes
    except Exception as e:
        print(f"Error occurred: {e}")  # Print the error message for debugging
    finally:
        cursor.close()

# Payment success route


@app.route('/payment/success')
def payment_success():
    session_id = request.args.get('session_id')

    # Retrieve the session information from Stripe
    checkout_session = stripe.checkout.Session.retrieve(session_id)

    # Retrieve the line items (the purchased course)
    line_items = stripe.checkout.Session.list_line_items(session_id)

    # Prepare the data for the receipt
    user_name = session.get('name')
    user_id = session.get('uid')  # Assuming the user ID is stored in session
    course_name = line_items.data[0].description
    amount = checkout_session.amount_total / 100  # Convert from paise to INR
    payment_date = datetime.fromtimestamp(checkout_session['created']).strftime(
        '%Y-%m-%d')  # Format as YYYY-MM-DD for MySQL
    print("# Prepare the data for the receipt")
    print("user_name"+str(user_name))
    print("user_id"+str(user_id))
    print("course_name"+str(course_name))
    print("amount"+str(amount))
    print("payment_date"+str(payment_date))
    # Get course_id from the metadata
    course_id = checkout_session.metadata['course_id']
    print("course_id"+str(course_id))

    # Insert payment details into the MySQL database
    insert_payment_details(
        payment_id=session_id, course_id=course_id, uid=user_id, purchase_amt=amount)

    # Render the receipt template
    return render_template('receipt.html', user_name=user_name, course_name=course_name, amount=amount, date=payment_date)

# Payment cancel route


@app.route('/payment/cancel')
def payment_cancel():
    return "Payment cancelled, please try again."

# Helper function to get course_id by name (example)


def get_course_id_by_name(course_name):

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(
        'SELECT course_id FROM course_list WHERE name = %s', (course_name,))
    course_id = cursor.fetchone()[0]
    return course_id


@app.route('/teacher_notes')
def teacher_notes():
    tid = session.get('uid')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(
        "SELECT tc.course_id, c.name FROM teacher_course tc JOIN course_list c ON tc.course_id = c.course_id WHERE tc.tid = %s",
        [tid]
    )
    courses = cursor.fetchall()
    cursor.close()
    # Render the notes.html page
    return render_template('teacher_notes.html', courses=courses)


@app.route('/upload_note', methods=['POST'])
def upload_note():
    tid = session.get('uid')
    note_name = request.form.get('note_name')
    course_id = request.form.get('course_id')

    print("Note Name:", note_name)
    print("Course ID:", course_id)

    if 'note_file' in request.files:
        file = request.files['note_file']

        # Ensure the file has a valid name
        if file.filename == '':
            return jsonify({'status': 'No selected file'}), 400

        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Insert into the database
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        sql_query = "INSERT INTO notes (note_name, course_id, link,tid) VALUES (%s, %s, %s,%s)"
        cursor.execute(sql_query, (note_name, course_id, filename, tid))

        # Commit the transaction
        mysql.connection.commit()

        return jsonify({'status': 'Note added successfully'})
    else:
        return jsonify({'status': 'File upload failed'}), 400


# Route to fetch past notes for a specific course
@app.route('/get_past_notes', methods=['POST'])
def get_past_notes():
    tid = session.get('uid')
    course_id = request.form['course_id']

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(
        "SELECT * FROM notes WHERE course_id = %s and tid = %s", (course_id, tid))
    notes = cursor.fetchall()

    return jsonify(notes)

# Route to update a note


@app.route('/update_note', methods=['POST'])
def update_note():
    nid = request.form.get('nid')  # Get the note ID
    note_name = request.form.get('note_name')  # Get the note name
    print(f"Note ID: {nid}")
    print(f"Note Name: {note_name}")

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Check if a file is being uploaded
    if 'note_file' in request.files:
        file = request.files['note_file']
        filename = secure_filename(file.filename)
        # Save the new file
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Update both name and file link in the database
        cursor.execute(
            "UPDATE notes SET note_name = %s, link = %s WHERE nid = %s", (note_name, filename, nid))
    else:
        # Only update the name if no file is uploaded
        cursor.execute(
            "UPDATE notes SET note_name = %s WHERE nid = %s", (note_name, nid))

    mysql.connection.commit()  # Commit changes
    return jsonify({'status': 'Note updated successfully'})


# Route to delete a note
@app.route('/delete_note', methods=['POST'])
def delete_note():
    nid = request.form['nid']
    # Convert to integer

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("DELETE FROM notes WHERE nid = %s", (nid,))
    mysql.connection.commit()  # Commit the transaction to apply changes

    # Check if the delete operation was successful
    if cursor.rowcount > 0:
        return jsonify({'status': 'Note deleted successfully'})
    else:
        # Return 404 if no rows were affected
        return jsonify({'status': 'Note not found'}), 404


@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
# Route to view a note (will open in a modal)


@app.route('/view_note', methods=['POST'])
def view_note():
    nid = request.form['nid']

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT link FROM notes WHERE nid = %s", (nid,))

    note = cursor.fetchone()
    # print(note,"dsadasdasdas")
    return jsonify(note)


@app.route('/notes')
def notes():
    tid = session.get('uid')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(
        "SELECT tc.course_id, c.name FROM teacher_course tc JOIN course_list c ON tc.course_id = c.course_id WHERE tc.tid = %s",
        [tid]
    )
    courses = cursor.fetchall()
    cursor.close()

    return render_template('notes.html', courses=courses)


@app.route('/schedule_class')
def schedule_class():
    tid = session.get('uid')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(
        "SELECT tc.course_id, c.name FROM teacher_course tc JOIN course_list c ON tc.course_id = c.course_id WHERE tc.tid = %s",
        [tid]
    )
    courses = cursor.fetchall()
    cursor.close()

    return render_template('schedule_class.html', courses=courses)

# Route to handle scheduling a class


@app.route('/set_class', methods=['POST'])
def set_class():
    tid = session.get('uid')
    course_id = request.form['course_id']
    class_date = request.form['class_date']
    class_time = request.form['class_time']
    description = request.form['description']
    online_link = request.form['online_link']

    try:
        # Convert the date and time to a datetime object
        class_datetime = datetime.strptime(
            f'{class_date} {class_time}', '%Y-%m-%d %H:%M')

        # Insert the scheduled class into the database
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            "INSERT INTO scheduled_classes (tid, course_id, class_datetime, description, online_link) VALUES (%s, %s, %s, %s, %s)",
            (tid, course_id, class_datetime, description, online_link)
        )
        mysql.connection.commit()
        cursor.close()

        return jsonify({'status': 'success', 'message': 'Class scheduled successfully!'})

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/student_detail')
def student_detail():
    if 'uid' not in session:
        return redirect('/login')  # Redirect if not logged in

    user_id = session['uid']
    student_name = session.get('name')

    # Fetch purchased courses for the student
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('''
        SELECT c.course_id, c.name, c.cost
        FROM purchase_detail pd
        JOIN course_list c ON pd.course_id = c.course_id
        WHERE pd.uid = %s
    ''', (user_id,))
    purchased_courses = cursor.fetchall()

    return render_template('student_detail.html', courses=purchased_courses, student_name=student_name)


@app.route('/course_details/<int:course_id>', methods=['GET'])
def course_details(course_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Fetch teacher assigned to the course
    # Get tid from teacher_course
    cursor.execute('''
        SELECT tid 
        FROM teacher_course 
        WHERE course_id = %s
    ''', (course_id,))
    tid_result = cursor.fetchone()

    teacher = None
    if tid_result:
        tid = tid_result['tid']
        # Now get the teacher's name from tbl_user using tid
        cursor.execute('''
            SELECT name AS teacher_name 
            FROM tbl_user 
            WHERE uid = %s
        ''', (tid,))
        teacher = cursor.fetchone()

    # Fetch notes associated with the course
    cursor.execute('''
        SELECT note_name
        FROM notes 
        WHERE course_id = %s
    ''', (course_id,))
    notes = cursor.fetchall()
    print(course_id)

    # Fetch scheduled classes for the course
    cursor.execute('''
        SELECT class_datetime,description
        FROM scheduled_classes 
        WHERE course_id = %s
    ''', (course_id,))
    schedule = cursor.fetchall()

    return jsonify({
        'teacher_name': teacher['teacher_name'] if teacher else 'No teacher assigned',
        'notes': notes,
        'schedule': schedule
    })


# NEW CODE CHANGE FOR  teacher_dashboard_show on 14-10-2024
@app.route('/teacher_schedule_class', methods=['GET', 'POST'])
def teacher_schedule_class():
    tid = session.get('uid')
    if not tid:
        return "User not logged in"

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Fetch the list of assigned courses for the teacher
    cursor.execute(
        "SELECT course_id, name FROM course_list WHERE course_id IN (SELECT course_id FROM teacher_course WHERE tid = %s)", (tid,))
    assigned_courses = cursor.fetchall()

    return render_template('teacher_schedule_class.html', courses=assigned_courses)


@app.route('/get_past_classes', methods=['POST'])
def get_past_classes():
    try:
        course_id = request.form.get('course_id')

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # Fetch the past classes for the given course_id
        cursor.execute(
            "SELECT scid, description, class_datetime FROM scheduled_classes WHERE course_id = %s", (course_id,))
        classes = cursor.fetchall()

        # Return classes as JSON response
        return jsonify(classes)

    except Exception as e:
        # This will output the error in your terminal or log
        print(f"Error: {e}")
        return jsonify({'status': 'error', 'message': 'An error occurred while fetching classes.'}), 500


@app.route('/get_class_details', methods=['GET'])
def get_class_details():
    scid = request.args.get('scid')

    # Create a cursor with DictCursor to fetch results as dictionaries
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    try:
        # SQL query to fetch class details
        sql_query = "SELECT scid, description, class_datetime, online_link FROM scheduled_classes WHERE scid = %s;"
        cursor.execute(sql_query, (scid,))
        result = cursor.fetchone()  # Fetch the first result

        if result:
            return jsonify(result)  # The result is already a dictionary
        else:
            return jsonify({'error': 'Class not found'}), 404

    finally:
        cursor.close()  # Close the cursor


@app.route('/add_class', methods=['POST'])
def add_class():
    tid = session.get('uid')
    course_id = request.form.get('course_id')
    description = request.form.get('description')
    class_datetime = request.form.get('class_datetime')
    online_link = request.form.get('online_link')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Insert new class data into the scheduled_class table
    cursor.execute("INSERT INTO scheduled_classes (tid, course_id, class_datetime, description, online_link) VALUES (%s, %s, %s, %s, %s)",
                   (tid, course_id, class_datetime, description, online_link))
    mysql.connection.commit()

    return jsonify({'status': 'Class added successfully'})


@app.route('/update_class', methods=['POST'])
def update_class():
    scid = request.form.get('scid')
    description = request.form.get('description')
    class_datetime = request.form.get('class_datetime')
    online_link = request.form.get('online_link')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Update class information
    cursor.execute("UPDATE scheduled_classes SET description=%s, class_datetime=%s, online_link=%s WHERE scid=%s",
                   (description, class_datetime, online_link, scid))
    mysql.connection.commit()

    return jsonify({'status': 'Class updated successfully'})


@app.route('/delete_class', methods=['POST'])
def delete_class():
    scid = request.form.get('scid')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Delete class
    cursor.execute("DELETE FROM scheduled_classes WHERE scid=%s", (scid,))
    mysql.connection.commit()

    return jsonify({'status': 'Class deleted successfully'})


@app.route('/teacher_assignment')
def teacher_assignment():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    cursor.execute(
        "SELECT course_id, name FROM course_list WHERE course_id IN (SELECT course_id FROM teacher_course WHERE tid = %s)", (session['uid'],))
    courses = cursor.fetchall()
    return render_template('teacher_assignment.html', courses=courses)

# Route to fetch assignments by course


@app.route('/get_assignments', methods=['POST'])
def get_assignments():
    course_id = request.form['course_id']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM assignments WHERE course_id = %s and uid = %s",
                   [course_id, session['uid']])
    assignments = cursor.fetchall()
    return jsonify(assignments)


ALLOWED_EXTENSIONS = {'pdf'}
# Route to create a new assignment


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/create_assignment', methods=['POST'])
def create_assignment():
    uid = session.get("uid")
    if 'assignment_file' not in request.files:
        flash('No file part')
        return redirect(request.url)

    file = request.files['assignment_file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)  # Secure the filename
        # Save the file
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Get other form fields
        assignment_name = request.form['assignment_name']
        deadline = request.form['deadline']
        # Assuming course_id comes from a dropdown
        course_id = request.form['course_id']

        # Insert into the database (example using MySQL)
        cursor = mysql.connection.cursor()
        cursor.execute("""
            INSERT INTO assignments (assignment_name, course_id, assignment_link, deadline,uid)
            VALUES (%s, %s, %s, %s, %s)
        """, (assignment_name, course_id, filename, deadline, uid))
        mysql.connection.commit()
        cursor.close()

        flash('Assignment uploaded successfully!')
        return redirect(url_for('teacher_assignment'))

    else:
        flash('Invalid file format! Only PDF files are allowed.')
        return redirect(request.url)


# Route to delete assignment
@app.route('/delete_assignment', methods=['POST'])
def delete_assignment():
    assignment_id = request.form['assignment_id']

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(
        "DELETE FROM assignments WHERE assignment_id = %s", [assignment_id])
    mysql.connection.commit()

    return jsonify({'status': 'Assignment deleted successfully'})

# Route to open/close an assignment


@app.route('/toggle_assignment', methods=['POST'])
def toggle_assignment():
    assignment_id = request.form['assignment_id']
    manual_open = request.form['manual_open']

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("UPDATE assignments SET manual_open = %s WHERE assignment_id = %s",
                   (manual_open, assignment_id))
    mysql.connection.commit()

    return jsonify({'status': 'Assignment status updated successfully'})

# Route to view student submissions


@app.route('/view_submissions', methods=['POST'])
def view_submissions():
    assignment_id = request.form['assignment_id']

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(
        "SELECT * FROM assignment_student WHERE assignment_id = %s", [assignment_id])
    submissions = cursor.fetchall()

    return jsonify(submissions)


@app.route('/view_assignment_document', methods=['POST'])
def view_assignment_document():
    assignment_id = request.form.get('assignment_id')
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Query to fetch the assignment document link
    cursor.execute(
        "SELECT assignment_link FROM assignments WHERE assignment_id = %s", [assignment_id])
    assignment = cursor.fetchone()

    if assignment:
        return jsonify(assignment)  # Return the assignment link
    else:
        return jsonify({'error': 'Assignment not found'}), 404


@app.route('/admin_add_module')
def admin_add_module():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT course_id, name FROM course_list")
    courses = cursor.fetchall()
    cursor.close()
    return render_template('admin_add_module.html', courses=courses)


@app.route('/get_subjects', methods=['POST'])
def get_subjects():
    course_id = request.form['course_id']
    cursor = mysql.connection.cursor()
    cursor.execute(
        "SELECT subject_id, subject_name FROM subject WHERE course_id = %s", (course_id,))
    subjects = cursor.fetchall()
    cursor.close()
    if not subjects:
        return jsonify({"status": "no_subjects", "message": "No subjects found for this course"})
    return jsonify(subjects)


@app.route('/get_modules', methods=['POST'])
def get_modules():
    subject_id = request.form['subject_id']
    cursor = mysql.connection.cursor()
    cursor.execute(
        "SELECT module_id, module_name, module_desc FROM module WHERE subject_id = %s", (subject_id,))
    modules = cursor.fetchall()
    cursor.close()
    return jsonify(modules)


@app.route('/add_module', methods=['POST'])
def add_module():
    subject_id = request.form['subject_id']
    module_name = request.form['module_name']
    module_desc = request.form['module_desc']
    cursor = mysql.connection.cursor()
    cursor.execute("INSERT INTO module (subject_id, module_name, module_desc) VALUES (%s, %s, %s)",
                   (subject_id, module_name, module_desc))
    mysql.connection.commit()
    cursor.close()
    return jsonify({"status": "success"})


@app.route('/edit_module', methods=['POST'])
def edit_module():
    module_id = request.form['module_id']
    module_name = request.form['module_name']
    module_desc = request.form['module_desc']
    cursor = mysql.connection.cursor()
    cursor.execute("UPDATE module SET module_name = %s, module_desc = %s WHERE module_id = %s",
                   (module_name, module_desc, module_id))
    mysql.connection.commit()
    cursor.close()
    return jsonify({"status": "success"})


@app.route('/delete_module', methods=['POST'])
def delete_module():
    module_id = request.form['module_id']
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM module WHERE module_id = %s", (module_id,))
    mysql.connection.commit()
    cursor.close()
    return jsonify({"status": "success"})


@app.route('/admin_create_timetable.html', methods=['GET', 'POST'])
def admin_create_timetable():
    # Fetch courses for dropdown
    cur = mysql.connection.cursor()
    cur.execute("SELECT course_id, name FROM course_list")
    courses = cur.fetchall()
    cur.close()

    return render_template('admin_create_timetable.html', courses=courses)


@app.route('/fetch_subjects/<int:course_id>')
def fetch_subjects(course_id):
    # Fetch assigned subjects based on selected course
    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT subject_id, subject_name FROM subject WHERE course_id = %s", (course_id,))
    subjects = cur.fetchall()
    cur.close()
    return jsonify(subjects)


@app.route('/fetch_time_slots/<int:course_id>/<string:class_day>/<string:subject>')
def fetch_time_slots(course_id, class_day, subject):
    # Check for available time slots
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT class_startime FROM timetable
        WHERE course_id = %s AND class_day = %s AND subject != %s
    """, (course_id, class_day, subject))
    assigned_slots = [row[0] for row in cur.fetchall()]
    cur.close()

    # Generate available time slots, exclude those already assigned
    all_slots = ['16:00', '17:00', '18:00', '19:00', '20:00']
    available_slots = [
        slot for slot in all_slots if slot not in assigned_slots]
    return jsonify(available_slots)


@app.route('/submit_timetable', methods=['POST'])
def submit_timetable():
    data = request.get_json()
    uid = data['uid']
    course_id = data['course_id']
    subject = data['subject']
    class_day = data['class_day']
    class_startime = data['class_startime']
    class_endtime = data['class_endtime']

    # Insert timetable data
    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO timetable (uid, course_id, subject, class_day, class_startime, class_endtime)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (uid, course_id, subject, class_day, class_startime, class_endtime))
    mysql.connection.commit()
    cur.close()

    return jsonify({"message": "Timetable entry added successfully!"})


@app.route('/check_conflict/<int:course_id>/<string:class_day>/<string:start_time>')
def check_conflict(course_id, class_day, start_time):
    # Check for existing assignments at the same time
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT subject FROM timetable
        WHERE course_id = %s AND class_day = %s AND class_startime = %s
    """, (course_id, class_day, start_time))
    conflict_subjects = cur.fetchall()
    cur.close()

    if conflict_subjects:
        # Return the first conflicting subject
        return jsonify({'conflict': True, 'subject': conflict_subjects[0][0]})
    return jsonify({'conflict': False})


@app.route('/admin_show_timetable', methods=['GET'])
def admin_show_timetable():
    # Fetch list of courses to populate dropdown
    cur = mysql.connection.cursor()
    cur.execute("SELECT course_id, name FROM course_list WHERE hide = 0")
    courses = cur.fetchall()
    cur.close()  # Close the cursor
    return render_template('admin_show_timetable.html', courses=courses)


@app.route('/fetch_timetable', methods=['GET'])
def fetch_timetable():
    course_id = request.args.get('course_id', type=int)
    day = request.args.get('day', type=str)

    cur = mysql.connection.cursor()

    # Step 1: Retrieve subject, start time, and end time from the timetable table
    query_timetable = """
        SELECT 
            subject, class_startime, class_endtime 
        FROM 
            timetable
        WHERE 
            course_id = %s AND class_day = %s
    """
    cur.execute(query_timetable, (course_id, day))
    timetable_entries = cur.fetchall()

    # Step 2: Manually map each entry to a dictionary
    timetable = []
    for entry in timetable_entries:
        subject_id = entry[0]   # 'subject' column
        start_time = entry[1]   # 'class_startime' column
        end_time = entry[2]     # 'class_endtime' column

        # Query to get subject_name for each subject_id
        cur.execute(
            "SELECT subject_name FROM subject WHERE subject_id = %s", (subject_id,))
        subject_name_result = cur.fetchone()
        subject_name = subject_name_result[0] if subject_name_result else "Unknown"

        # Append the result to the timetable list, converting time to string
        timetable.append({
            "class_startime": str(start_time),
            "class_endtime": str(end_time),
            "subject_name": subject_name
        })

    cur.close()

    return jsonify(timetable)


# teacher_sentimant
# Load pre-trained GloVe model and BERT model
glove_model = gensim.models.KeyedVectors.load("glove_wiki_gigaword_300.model")
bert_model = pipeline("sentiment-analysis")

# Define positive, negative, and filler words
positive_words = [
    'excellent', 'outstanding', 'fantastic', 'great', 'wonderful', 'amazing', 'super', 'impressive',
    'brilliant', 'skilled', 'knowledgeable', 'dedicated', 'helpful', 'supportive', 'encouraging',
    'friendly', 'professional', 'engaging', 'motivating', 'remarkable', 'exceptional', 'awesome',
    'reliable', 'trustworthy', 'innovative', 'enthusiastic', 'proficient', 'talented', 'competent',
    'effective', 'efficient', 'passionate', 'creative', 'insightful', 'adaptable', 'organized',
    'patient', 'resourceful', 'visionary', 'collaborative', 'appreciative', 'polished', 'positive'
]

negative_words = [
    'poor', 'bad', 'awful', 'horrible', 'inadequate', 'unsatisfactory', 'ineffective', 'unhelpful',
    'disappointing', 'unprofessional', 'dull', 'boring', 'incompetent', 'rude', 'disorganized',
    'unprepared', 'unresponsive', 'indifferent', 'slow', 'confusing', 'biased', 'unreliable',
    'unpleasant', 'uncaring', 'unfriendly', 'unmotivated', 'undependable', 'untrustworthy',
    'unproductive', 'unapproachable', 'unskilled', 'unqualified', 'unreceptive', 'unconcerned',
    'unimpressive', 'underwhelming', 'uncooperative', 'unenthusiastic', 'unforgiving', 'uncertain',
    'dishonest', 'inefficient', 'inconsistent', 'impolite', 'disorganized', 'inconsiderate',
    'apathetic', 'hostile', 'negligent', 'disengaged', 'callous'
]


filler_words = [
    'like', 'uh', 'um', 'you', 'know', 'just', 'sort', 'of', 'kind', 'this', 'that', 'actually',
    'basically', 'literally', 'seriously', 'not', 'want', 'I', 'he', 'she', 'him', 'her',
    'they', 'them', 'there', 'if', 'that', 'thing', 'really', 'so', 'right', 'well', 'got',
    'maybe', 'could', 'might', 'sort', 'gonna', 'kinda', 'pretty', 'look', 'see', 'feel',
    'get', 'would', 'should', 'do', 'did', 'has', 'have', 'having', 'been', 'am', 'are',
    'is', 'was', 'were'
]


def get_word_vectors(words):
    return {word: glove_model[word] for word in words if word in glove_model}


def prepare_data():
    word_lists = {'positive': positive_words,
                  'negative': negative_words, 'filler': filler_words}
    X = []
    y = []

    for label, words in word_lists.items():
        vectors = get_word_vectors(words)
        if vectors:
            X.extend(vectors.values())
            y.extend([label] * len(vectors))

    return np.array(X), np.array(y)


def classify_words_knn(sentence, knn_model):
    words = tokenize_sentence(sentence)
    words_in_model = get_word_vectors(words)

    classifications = {}
    for word, vector in words_in_model.items():
        predicted_label = knn_model.predict([vector])[0]
        # Exclude filler words from classification results
        if predicted_label != 'filler':
            classifications[word] = predicted_label

    return classifications


def tokenize_sentence(sentence):
    return sentence.lower().split()


@app.route('/teacher_view_sentiment')
def teacher_view_sentiment():
    teacher_uid = session.get('uid')

    # Retrieve reviews from the database
    cur = mysql.connection.cursor()
    cur.execute("SELECT review FROM review WHERE teacher = %s", (teacher_uid,))
    reviews = cur.fetchall()
    cur.close()

    # Use tuple indexing to access review text
    sentences = [review[0] for review in reviews]

    if not sentences:
        return jsonify({"error": "No reviews found"}), 404

    # Prepare and train KNN model
    X, y = prepare_data()
    knn_model = KNeighborsClassifier(n_neighbors=3)
    knn_model.fit(X, y)

    all_classifications = {}
    positive_count = 0
    negative_count = 0
    sentence_sentiments = []

    positive_sentence_count = 0
    negative_sentence_count = 0

    for sentence in sentences:
        classified_words = classify_words_knn(sentence, knn_model)
        all_classifications[sentence] = classified_words

        sentence_positive_count = sum(
            1 for word, label in classified_words.items() if label == 'positive')
        sentence_negative_count = sum(
            1 for word, label in classified_words.items() if label == 'negative')

        positive_count += sentence_positive_count
        negative_count += sentence_negative_count

        # Analyze sentence with BERT
        bert_result = bert_model(sentence)[0]
        sentiment_label = bert_result['label']
        print(f"Sentence: {sentence} - Sentiment Label: {sentiment_label}")
        sentiment_score = bert_result['score']
        sentence_sentiments.append({
            'sentence': sentence,
            'label': sentiment_label,
            'score': sentiment_score
        })

        # Count positive and negative sentences based on BERT labels
        if sentiment_label == 'POSITIVE':
            positive_sentence_count += 1
        elif sentiment_label == 'NEGATIVE':
            negative_sentence_count += 1

    total_words = positive_count + negative_count
    word_percentage = {
        'positive_percentage': (positive_count / total_words * 100) if total_words else 0,
        'negative_percentage': (negative_count / total_words * 100) if total_words else 0
    }

    # Calculate sentence percentage based on positive and negative sentence counts
    total_sentences = positive_sentence_count + negative_sentence_count
    sentence_percentage = {
        'positive_percentage': (positive_sentence_count / total_sentences * 100) if total_sentences else 0,
        'negative_percentage': (negative_sentence_count / total_sentences * 100) if total_sentences else 0
    }
    print(sentence_percentage['positive_percentage'])
    return render_template('teacher_view_sentiment.html',
                           word_percentage=word_percentage,
                           sentence_percentage=sentence_percentage,
                           sentence_sentiments=sentence_sentiments,
                           all_classifications=all_classifications)


@app.route('/teacher_view_past_classes', methods=['GET'])
def teacher_view_past_classes():
    # Get teacher ID (e.g., from session)
    tid = session.get('uid')  # Adjust based on actual session variable name
    if not tid:
        return "Teacher ID not found in session", 400

    # Fetch assigned courses for the teacher
    cur = mysql.connection.cursor()
    cur.execute("SELECT course_id, name FROM course_list WHERE course_id IN (SELECT course_id FROM teacher_course WHERE tid = %s)", (tid,))
    courses = cur.fetchall()  # Use fetchall() to retrieve the result set as an iterable
    cur.close()  # Close the cursor after query execution

    # Debugging: print the fetched courses to check if data is retrieved correctly
    print("Fetched courses:", courses)

    return render_template('teacher_view_past_classes.html', courses=courses)


@app.route('/get_past_class_rec', methods=['POST'])
def get_past_class_rec():
    course_id = request.form.get('course_id')
    current_time = datetime.now()
    cur = mysql.connection.cursor()
    cur.execute("SELECT scid, class_datetime, description, recording FROM scheduled_classes WHERE course_id = %s AND class_datetime < %s", (course_id, current_time))
    past_classes = cur.fetchall()

    classes_list = [
        {
            'scid': class_[0],
            'class_datetime': class_[1],
            'description': class_[2],
            'recording': class_[3]
        } for class_ in past_classes
    ]

    cur.close()
    return jsonify(past_classes=classes_list)


@app.route('/upload_recording/<int:scid>', methods=['POST'])
def upload_recording(scid):
    file = request.files['file']
    filepath = None

    if file:
        filepath = os.path.join('uploads', file.filename)
        file.save(filepath)

        cur = mysql.connection.cursor()
        cur.execute(
            "UPDATE scheduled_classes SET recording = %s WHERE scid = %s", (filepath, scid))
        mysql.connection.commit()
        cur.close()

    return jsonify(success=True, filepath=filepath)


@app.route('/delete_recording/<int:scid>', methods=['POST'])
def delete_recording(scid):
    cur = mysql.connection.cursor()
    cur.execute(
        "UPDATE scheduled_classes SET recording = NULL WHERE scid = %s", (scid,))
    mysql.connection.commit()
    cur.close()

    return jsonify(success=True)


@app.route('/student_assigned_course')
def student_assigned_course():
    # Retrieve the user ID from session
    uid = session['uid']

    # Query to get course_id from purchase_detail for the current student
    cur = mysql.connection.cursor()
    cur.execute("SELECT course_id FROM purchase_detail WHERE uid = %s", (uid,))
    course_data = cur.fetchone()

    if not course_data:
        return "No course purchased", 404

    course_id = course_data[0]

    # Get course name and description from course_list
    cur.execute(
        "SELECT name, cours_desc FROM course_list WHERE course_id = %s", (course_id,))
    course_info = cur.fetchone()
    course_name, course_desc = course_info if course_info else (
        "Unknown Course", "No Description Available")

    # Get teacher names for the course
    cur.execute("""
        SELECT tbl_user.name 
        FROM teacher_course 
        INNER JOIN tbl_user ON teacher_course.tid = tbl_user.uid
        WHERE teacher_course.course_id = %s
    """, (course_id,))
    teacher_names = [row[0] for row in cur.fetchall()]

    cur.close()

    return render_template('student_assigned_course.html', course_name=course_name, course_desc=course_desc, teacher_names=teacher_names)


@app.route('/student_current_class')
def student_current_class():
    uid = session.get('uid')
    cur = mysql.connection.cursor()

    # Get courses purchased by the user
    cur.execute("SELECT p.course_id, c.name FROM purchase_detail p JOIN course_list c ON p.course_id = c.course_id WHERE p.uid = %s", (uid,))
    courses = cur.fetchall()  # [(course_id, course_name), ...]

    cur.close()
    return render_template('student_current_class.html', courses=courses)


@app.route('/student_get_class_details', methods=['POST'])
def student_get_class_details():
    course_id = request.form.get('course_id')
    current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    cur = mysql.connection.cursor()

    # Query for current day's classes with time after current time
    cur.execute("""
        SELECT sc.class_datetime, sc.description, sc.online_link, u.name
        FROM scheduled_classes sc
        JOIN tbl_user u ON sc.tid = u.uid
        WHERE sc.course_id = %s
        AND DATE(sc.class_datetime) = CURDATE()
        AND sc.class_datetime > %s
    """, (course_id, current_datetime))

    # [(class_datetime, description, online_link, teacher_name), ...]
    classes = cur.fetchall()

    cur.close()

    # Format the results as a JSON response
    class_details = []
    for class_ in classes:
        class_datetime = class_[0]
        formatted_date = class_datetime.strftime('%d/%m/%Y')
        formatted_time = class_datetime.strftime('%I:%M %p')
        class_details.append({
            'date': formatted_date,
            'time': formatted_time,
            'teacher': class_[3],
            'description': class_[1],
            'online_link': class_[2]
        })

    return jsonify(class_details)


@app.route('/student_see_recording', methods=['GET'])
def student_see_recording():
    # Retrieve the student ID from session
    uid = session.get('uid')
    if not uid:
        return "User not logged in", 401

    # Get the courses purchased by the student
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT c.course_id, c.name 
        FROM course_list c
        JOIN purchase_detail p ON c.course_id = p.course_id
        WHERE p.uid = %s
    """, (uid,))
    courses = cur.fetchall()
    cur.close()

    # Render the template with the courses list
    return render_template('student_see_recording.html', courses=courses)


@app.route('/student_get_past_classes', methods=['POST'])
def student_get_past_classes():
    course_id = request.form.get('course_id')
    current_time = datetime.now()

    # Retrieve past classes for the selected course
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT scid, class_datetime, description, recording 
        FROM scheduled_classes 
        WHERE course_id = %s AND class_datetime < %s
    """, (course_id, current_time))
    past_classes = cur.fetchall()
    cur.close()

    # Format data to send as JSON response
    classes_list = []
    for class_ in past_classes:
        classes_list.append({
            'scid': class_[0],
            'class_datetime': class_[1],
            'description': class_[2],
            'recording': class_[3]
        })

    return jsonify(past_classes=classes_list)


@app.route('/student_view_notes', methods=['GET'])
def student_view_notes():
    # Retrieve user ID from session
    uid = session.get('uid')
    if not uid:
        return "User not logged in", 401

    # Fetch courses purchased by the student
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT c.course_id, c.name 
        FROM course_list c
        JOIN purchase_detail p ON c.course_id = p.course_id
        WHERE p.uid = %s
    """, (uid,))
    courses = cur.fetchall()
    cur.close()

    # Render the template with courses
    return render_template('student_view_notes.html', courses=courses)


@app.route('/get_notes', methods=['POST'])
def get_notes():
    course_id = request.form.get('course_id')

    # Fetch notes for the selected course along with the teacher's name
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT n.nid, n.note_name, n.link, u.name AS teacher_name
        FROM notes n
        JOIN tbl_user u ON n.tid = u.uid
        WHERE n.course_id = %s
    """, (course_id,))
    notes = cur.fetchall()
    cur.close()

    # Format data to send as JSON response
    notes_list = []
    for note in notes:
        notes_list.append({
            'nid': note[0],
            'note_name': note[1],
            'link': note[2],
            'teacher_name': note[3]
        })

    return jsonify(notes=notes_list)


@app.route('/student_manage_review', methods=['GET'])
def student_manage_review():
    # Retrieve user ID from session
    uid = session.get('uid')
    if not uid:
        return "User not logged in", 401

    # Fetch course IDs purchased by the student
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT course_id FROM purchase_detail WHERE uid = %s
    """, (uid,))
    purchased_courses = cur.fetchall()

    # Fetch teachers associated with purchased courses
    teachers = []
    for course in purchased_courses:
        course_id = course[0]
        cur.execute("""
            SELECT t.uid, t.name
            FROM tbl_user t
            JOIN teacher_course tc ON t.uid = tc.tid
            WHERE tc.course_id = %s
        """, (course_id,))
        teachers.extend(cur.fetchall())

    cur.close()

    # Render the template with teachers data
    return render_template('student_manage_review.html', teachers=teachers)


@app.route('/get_review', methods=['POST'])
def get_review():
    uid = session.get('uid')
    teacher_id = request.form.get('teacher_id')

    # Fetch existing review if it exists
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT review FROM review
        WHERE student = %s AND teacher = %s
    """, (uid, teacher_id))
    review_data = cur.fetchone()
    cur.close()

    # Return the review data
    return jsonify(review=review_data[0] if review_data else None)


@app.route('/save_review', methods=['POST'])
def save_review():
    uid = session.get('uid')
    teacher_id = request.form.get('teacher_id')
    review_text = request.form.get('review')

    # Check if a review already exists
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT rid FROM review
        WHERE student = %s AND teacher = %s
    """, (uid, teacher_id))
    existing_review = cur.fetchone()

    # Insert new review or update existing review
    if existing_review:
        cur.execute("""
            UPDATE review SET review = %s
            WHERE rid = %s
        """, (review_text, existing_review[0]))
    else:
        cur.execute("""
            INSERT INTO review (review, student, teacher)
            VALUES (%s, %s, %s)
        """, (review_text, uid, teacher_id))
    mysql.connection.commit()
    cur.close()

    return jsonify(status="success")


@app.route('/delete_review', methods=['POST'])
def delete_review():
    uid = session.get('uid')
    teacher_id = request.form.get('teacher_id')

    # Delete review
    cur = mysql.connection.cursor()
    cur.execute("""
        DELETE FROM review
        WHERE student = %s AND teacher = %s
    """, (uid, teacher_id))
    mysql.connection.commit()
    cur.close()

    return jsonify(status="deleted")


if __name__ == "__main__":
    app.run(debug=True)
