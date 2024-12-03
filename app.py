import sqlite3
from flask import Flask, render_template, request, url_for, flash, redirect, session, flash

app = Flask(__name__)
app.config["DEBUG"] = True
app.config['SECRET_KEY'] = 'your secret key'

def get_db_connection():
    conn = sqlite3.connect('reservations.db')
    conn.row_factory = sqlite3.Row
    try:
        conn.execute('SELECT 1 FROM admins LIMIT 1')
    except sqlite3.OperationalError:
        print("Error: 'admins' table does not exist.")
        raise
    return conn

def get_cost_matrix():
    cost_matrix = [[100, 75, 50, 100] for row in range(12)]
    return cost_matrix

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        selected_option = request.form.get('menu_option')
        if not selected_option:
            flash("You must select an option", "error")
            return redirect(url_for('index'))
        if selected_option == 'admin_login':
            return redirect(url_for('login'))
        elif selected_option == 'reserve_seat':
            return redirect(url_for('reservations'))
    return render_template('index.html')


@app.route('/admin/')
def admin():
    conn = get_db_connection()
    reservations = conn.execute('SELECT seatRow, seatColumn FROM reservations').fetchall()
    conn.close()
    rows, cols = 12, 4
    seat_chart = [['O' for _ in range(cols)] for _ in range(rows)]
    cost_matrix = get_cost_matrix()
    total_sales = 0
    for reservation in reservations:
        row, col = reservation['seatRow'], reservation['seatColumn']
        seat_chart[row][col] = 'X'
        total_sales += cost_matrix[row][col]
    return render_template('admin.html', seat_chart=seat_chart, total_sales=total_sales)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM admins WHERE username = ? AND password = ?', (username, password)).fetchone()
        conn.close()
        if user:
            session['user_id'] = user['username']
            return redirect(url_for('admin'))
        else:
            flash("Invalid username or password", "error")
    
    return render_template('login.html')

@app.route('/reservations', methods=['GET', 'POST'])
def reservations():
    conn = get_db_connection()
    existing_reservations = conn.execute('SELECT seatRow, seatColumn FROM reservations').fetchall()
    rows, cols = 12, 4
    seat_chart = [['O' for _ in range(cols)] for _ in range(rows)]
    for reservation in existing_reservations:
        seat_chart[reservation['seatRow']][reservation['seatColumn']] = 'X'
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        row = int(request.form['row'])
        column = int(request.form['column'])
        eTicketNumber = None
        if seat_chart[row][column] == 'X':
            flash("That seat is already taken. Please choose another seat.", "error")
        else:
            base_string = "INFOTC4320"
            eTicketNumber = "".join(
                char for pair in zip(first_name, base_string) for char in pair
            )
            eTicketNumber += first_name[len(base_string):] if len(first_name) > len(base_string) else base_string[len(first_name):]
            conn.execute(
                'INSERT INTO reservations (passengerName, seatRow, seatColumn, eTicketNumber) VALUES (?, ?, ?, ?)',
                (f"{first_name} {last_name}", row, column, eTicketNumber)
            )
            conn.commit()
            flash(f"Reservation successful for Row:{row + 1}, Seat:{column + 1}. Your eTicket Number is: {eTicketNumber}", "success")
        existing_reservations = conn.execute('SELECT seatRow, seatColumn FROM reservations').fetchall()
        for reservation in existing_reservations:
            seat_chart[reservation['seatRow']][reservation['seatColumn']] = 'X'
    conn.close()
    return render_template('reservations.html', seat_chart=seat_chart)

app.run()