from flask import Flask, render_template, redirect, request, url_for, session, flash, g
import mysql.connector
from mysql.connector import Error

e_id=0

# Flask app initialization
app2 = Flask(__name__, 
            template_folder='../client',
            static_folder='../client/static',
            static_url_path='/static')
app2.secret_key = "abc"

# MySQL configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '123456',
    'database': 'employee_management',
    'charset': 'utf8mb4'
}

# Create MySQL connection function
def get_db():
    if not hasattr(g, 'mysql_db'):
        try:
            g.mysql_db = mysql.connector.connect(**db_config)
        except Error as e:
            print(f"Error connecting to database: {e}")
            g.mysql_db = None
    return g.mysql_db

def execute_db(query, args=(), commit=False):
    conn = get_db()
    if conn is None:
        print("No database connection available")
        return None
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(query, args)
        if commit:
            conn.commit()
        try:
            has_rows = getattr(cur, 'with_rows', None)
        except Exception:
            has_rows = None
        if has_rows:
            result = cur.fetchall()
        else:
            result = []
        cur.close()
        return result
    except Exception as e:
        print(f"Database error: {e}")
        if commit and conn.is_connected():
            conn.rollback()
        return None

@app2.teardown_appcontext
def close_db(error):
    if hasattr(g, 'mysql_db'):
        g.mysql_db.close()

@app2.route('/')
def home():
    return redirect(url_for('login'))

@app2.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        global e_id
        e_id = request.form['e_id']
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        if role=='Employee':
            data = execute_db("SELECT * FROM emp_login WHERE emp_id = %s and emp_username=%s and emp_password=%s", 
                            (e_id,username,password))
            if not data or len(data)!=1:
                return redirect(url_for('registration'))
            else:
                return redirect(url_for('sepm'))
        elif role=='Admistrator':
            data = execute_db("SELECT * FROM admin_login WHERE admin_id = %s and admin_username=%s and admin_password=%s", 
                            (e_id,username,password))
            if not data or len(data)!=1:
                return redirect(url_for('registration'))
            else:
                return redirect(url_for('sepm'))
        return redirect(url_for('login'))
    else:
        return render_template('login.html')

@app2.route('/registration', methods=['GET', 'POST'])
def registration():
    if request.method == 'POST':
        global e_id
        e_id = request.form['e_id']
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        if role=='Employee':
            execute_db("INSERT INTO emp_login VALUES (%s, %s, %s)", (e_id,username,password), commit=True)
        elif role=='Admistrator':
            execute_db("INSERT INTO admin_login VALUES (%s, %s, %s)", (e_id,username,password), commit=True)
        return redirect(url_for('login'))
    else:
        return render_template('registration.html')

@app2.route('/sepm', methods=['GET', 'POST'])
def sepm():
    if not e_id:
        return redirect(url_for('login'))
    return render_template('index.html')

# --- OFFICIAL DETAILS ROUTES ---

@app2.route('/official', methods=['GET', 'POST'])
def official():
    if request.method == 'POST':
        return render_template('official.html')
    else:
        rows = execute_db("SELECT * FROM official")
        return render_template("official.html", rows = rows)

@app2.route('/add_employee', methods=['POST'])
def add_employee():
    data = request.form
    query = """
        INSERT INTO official (id, name, join_date, designation, department, monthly_salary, email, phone_num)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    execute_db(query, (
        data['id'], data['name'], data['join_date'], data['designation'],
        data['department'], data['monthly_salary'], data['email'], data['phone_num']
    ), commit=True)
    return redirect(url_for('official'))

@app2.route('/update_employee', methods=['POST'])
def update_employee():
    data = request.form
    query = """
        UPDATE official
        SET name=%s, email=%s, phone_num=%s, department=%s, designation=%s, monthly_salary=%s
        WHERE id=%s
    """
    execute_db(query, (
        data['name'], data['email'], data['phone'], data['department'],
        data['designation'], data['monthly_salary'], data['e_id']
    ), commit=True)
    return redirect(url_for('official'))

@app2.route('/delete_employee/<int:emp_id>', methods=['POST'])
def delete_employee(emp_id):
    conn = get_db()
    if conn is None:
        return redirect(url_for('official'))
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM salary WHERE emp_id = %s", (emp_id,))
        cursor.execute("DELETE FROM attendance WHERE emp_id = %s", (emp_id,))
        cursor.execute("DELETE FROM leaves WHERE emp_id = %s", (emp_id,))
        cursor.execute("DELETE FROM admin_login WHERE admin_id = %s", (emp_id,))
        cursor.execute("DELETE FROM emp_login WHERE emp_id = %s", (emp_id,))
        cursor.execute("DELETE FROM official WHERE id = %s", (emp_id,))
        conn.commit()
        cursor.close()
    except Exception as e:
        if conn.is_connected():
            conn.rollback()
        print(f"Error deleting employee: {e}")
    return redirect(url_for('official'))

# --- SALARY ROUTES (UPDATED) ---

@app2.route('/salary', methods=['GET', 'POST'])
def salary():
    # UPDATED: Joins with official table to show names for ALL employees
    if request.method == 'POST':
        return render_template('salary.html', rows=[])
    else:
        query = """
            SELECT official.id AS emp_id, official.name, 
                   salary.monthly_salary, salary.bonus, salary.deduction 
            FROM salary
            JOIN official ON salary.emp_id = official.id
        """
        rows = execute_db(query)
        return render_template("salary.html", rows=rows)

@app2.route('/add_salary', methods=['POST'])
def add_salary():
    data = request.form
    execute_db("INSERT INTO salary (emp_id, monthly_salary, bonus, deduction) VALUES (%s, %s, %s, %s)",
               (data.get('emp_id'), data.get('monthly_salary'), data.get('bonus', 0), data.get('deduction', 0)), commit=True)
    return redirect(url_for('salary'))

@app2.route('/update_salary', methods=['POST'])
def update_salary():
    data = request.form
    execute_db("UPDATE salary SET monthly_salary=%s, bonus=%s, deduction=%s WHERE emp_id=%s",
               (data.get('monthly_salary'), data.get('bonus'), data.get('deduction'), data.get('emp_id')), commit=True)
    return redirect(url_for('salary'))

@app2.route('/delete_salary/<int:emp_id>', methods=['POST'])
def delete_salary(emp_id):
    execute_db("DELETE FROM salary WHERE emp_id = %s", (emp_id,), commit=True)
    return redirect(url_for('salary'))

# --- ATTENDANCE ROUTES (UPDATED) ---

@app2.route('/attendance', methods=['GET', 'POST'])
def attendance():
    # UPDATED: Joins with official table to show names for ALL employees
    if request.method == 'POST':
        return render_template('attendance.html', rows=[])
    else:
        query = """
            SELECT official.id AS emp_id, official.name, 
                   attendance.entry_time, attendance.exit_time
            FROM attendance
            JOIN official ON attendance.emp_id = official.id
        """
        rows = execute_db(query)
        return render_template("attendance.html", rows=rows)

@app2.route('/add_attendance', methods=['POST'])
def add_attendance():
    data = request.form
    execute_db("INSERT INTO attendance (emp_id, entry_time, exit_time) VALUES (%s, %s, %s)",
               (data.get('emp_id'), data.get('entry_time'), data.get('exit_time')), commit=True)
    return redirect(url_for('attendance'))

@app2.route('/delete_attendance/<int:emp_id>', methods=['POST'])
def delete_attendance(emp_id):
    execute_db("DELETE FROM attendance WHERE emp_id = %s", (emp_id,), commit=True)
    return redirect(url_for('attendance'))

@app2.route('/update_attendance', methods=['POST'])
def update_attendance():
    data = request.form
    emp_id = data.get('emp_id')
    entry = data.get('entry_time')
    exit_time = data.get('exit_time')
    execute_db("UPDATE attendance SET entry_time=%s, exit_time=%s WHERE emp_id=%s",
               (entry, exit_time, emp_id), commit=True)
    return redirect(url_for('attendance'))

@app2.route('/update_entry', methods=['GET', 'POST'])
def entry_time():
    if request.method == 'GET':
        return render_template('attendance.html')
    else:
        e_id_form = request.form['e_id']
        entry = request.form['entry']
        execute_db("UPDATE attendance SET entry_time= %s WHERE emp_id = %s", 
                (entry,e_id_form), commit=True)
        return redirect(url_for('attendance'))

@app2.route('/update_exit', methods=['GET', 'POST'])
def exit_time():
    if request.method == 'GET':
        return render_template('attendance.html')
    else:
        e_id_form = request.form['e_id']
        exittime = request.form['exittime']
        execute_db("UPDATE attendance SET exit_time= %s WHERE emp_id = %s", 
                (exittime,e_id_form), commit=True)
        return redirect(url_for('attendance'))

# --- LEAVES ROUTES (UPDATED) ---

@app2.route('/leaves', methods=['GET', 'POST'])
def leaves():
    # UPDATED: Joins with official table to show names for ALL employees
    if request.method == 'POST':
        return render_template('leaves.html', rows=[])
    else:
        query = """
            SELECT official.id AS emp_id, official.name, 
                   leaves.leaves_allowed, leaves.leaves_taken, leaves.leaves_left
            FROM leaves
            JOIN official ON leaves.emp_id = official.id
        """
        rows = execute_db(query)
        return render_template("leaves.html", rows=rows)

@app2.route('/add_leaves', methods=['POST'])
def add_leaves():
    data = request.form
    execute_db("INSERT INTO leaves (emp_id, leaves_allowed, leaves_taken, leaves_left) VALUES (%s, %s, %s, %s)",
               (data.get('emp_id'), data.get('leaves_allowed'), data.get('leaves_taken'), data.get('leaves_left')), commit=True)
    return redirect(url_for('leaves'))

@app2.route('/update_leaves', methods=['POST'])
def update_leaves():
    data = request.form
    execute_db("UPDATE leaves SET leaves_allowed=%s, leaves_taken=%s, leaves_left=%s WHERE emp_id=%s",
               (data.get('leaves_allowed'), data.get('leaves_taken'), data.get('leaves_left'), data.get('emp_id')), commit=True)
    return redirect(url_for('leaves'))

@app2.route('/delete_leaves/<int:emp_id>', methods=['POST'])
def delete_leaves(emp_id):
    execute_db("DELETE FROM leaves WHERE emp_id = %s", (emp_id,), commit=True)
    return redirect(url_for('leaves'))

# --- OTHER ROUTES ---

@app2.route('/login_cred', methods=['GET', 'POST'])
def login_cred():
    if request.method == 'POST':
        return render_template('login_cred.html')
    else:
        global e_id
        # Note: Login credentials probably still want to filter by the current user?
        # If you want ALL login creds, remove "WHERE emp_id = %s"
        rows = execute_db("SELECT * FROM emp_login WHERE emp_id = %s", (e_id,))
        return render_template("login_cred.html", rows = rows)

@app2.route('/editusername', methods=['GET', 'POST'])
def edit_uname():
    if request.method == 'GET':
        return render_template('login_cred.html')
    else:
        e_id_form = request.form['e_id']
        username = request.form['username']
        execute_db("UPDATE emp_login SET emp_username= %s WHERE emp_id = %s", 
                (username,e_id_form), commit=True)
        return redirect(url_for('login_cred'))

@app2.route('/editpwd', methods=['GET', 'POST'])
def edit_pwd():
    if request.method == 'GET':
        return render_template('login_cred.html')
    else:
        e_id_form = request.form['e_id']
        password = request.form['password']
        execute_db("UPDATE emp_login SET emp_password= %s WHERE emp_id = %s", 
                (password,e_id_form), commit=True)
        return redirect(url_for('login_cred'))

@app2.route('/edit_name', methods=['GET', 'POST'])
def name():
    if request.method == 'GET':
        return render_template('official.html')
    else:
        e_id_form = request.form['e_id']
        name2 = request.form['name']
        execute_db("UPDATE official SET name= %s WHERE id = %s", 
                (name2,e_id_form), commit=True)
        return redirect(url_for('official'))

@app2.route('/edit_email', methods=['GET', 'POST'])
def emailid():
    if request.method == 'GET':
        return render_template('official.html')
    else:
        e_id_form = request.form['e_id']
        email = request.form['email']
        execute_db("UPDATE official SET email= %s WHERE id = %s", 
                (email,e_id_form), commit=True)
        return redirect(url_for('official'))

@app2.route('/edit_phone', methods=['GET', 'POST'])
def phonenum():
    if request.method == 'GET':
        return render_template('official.html')
    else:
        e_id_form = request.form['e_id']
        phone = request.form['phone']
        execute_db("UPDATE official SET phone= %s WHERE id = %s", 
                (phone,e_id_form), commit=True)
        return redirect(url_for('official'))

if __name__=="__main__":
    app2.run(debug=True)