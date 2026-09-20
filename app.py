from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import date

app = Flask(__name__)
app.secret_key = 'oilgas_secret_key_123'
DB_NAME = 'oilgas.db'

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS wells (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        location TEXT,
        type TEXT,
        drill_date DATE
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS production (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        well_id INTEGER,
        well_name TEXT,
        prod_date DATE,
        oil_barrels REAL DEFAULT 0,
        gas_mcf REAL DEFAULT 0,
        FOREIGN KEY (well_id) REFERENCES wells(id),
        UNIQUE(well_name, prod_date)
    )''')
    conn.commit()
    conn.close()


with app.app_context():
    init_db()

@app.route('/')
def dashboard():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM wells ORDER BY id DESC")
    wells = c.fetchall()
    c.execute("SELECT SUM(oil_barrels) as total_oil, SUM(gas_mcf) as total_gas FROM production")
    totals = c.fetchone()
    conn.close()
    return render_template('dashboard.html', wells=wells, totals=totals)

@app.route('/add_well', methods=['GET', 'POST'])
def add_well():
    if request.method == 'POST':
        name = request.form['well_name']
        location = request.form['location']
        type = request.form['type']
        drill_date = request.form['drill_date']
        try:
            conn = get_db()
            c = conn.cursor()
            c.execute("INSERT INTO wells (name, location, type, drill_date) VALUES (?,?,?,?)",
                      (name, location, type, drill_date))
            conn.commit()
            conn.close()
            flash('Well added successfully!', 'success')
            return redirect(url_for('dashboard'))
        except sqlite3.IntegrityError:
            flash('Well name already exists!', 'danger')
    return render_template('add_well.html', today=date.today().isoformat())

@app.route('/add_production', methods=['GET','POST'])
def add_production():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, name FROM wells ORDER BY name")
    wells = c.fetchall()
    today = date.today().isoformat()

    if request.method == 'POST':
        well_id = request.form['well_id']
        well_name = request.form['well_name']
        prod_date = request.form['prod_date']
        oil = request.form['oil_barrels']
        gas = request.form['gas_mcf']
        try:
            c.execute("INSERT INTO production (well_id, well_name, prod_date, oil_barrels, gas_mcf) VALUES (?,?,?,?,?)",
                      (well_id, well_name, prod_date, oil, gas))
            conn.commit()
            flash('Production data added!', 'success')
            return redirect(url_for('reports'))
        except sqlite3.IntegrityError:
            flash('Data for this well and date already exists!', 'danger')
        except Exception as e:
            flash(f'Error: {e}', 'danger')
        finally:
            conn.close()
    else:
        conn.close()
    return render_template('add_production.html', wells=wells, today=today)

@app.route('/reports')
def reports():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM production ORDER BY prod_date DESC")
    production_data = c.fetchall()
    conn.close()
    return render_template('reports.html', data=production_data)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
