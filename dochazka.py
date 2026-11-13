from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import uuid
import qrcode
import io
import base64

app = Flask(__name__)
DB_NAME = 'test_dochazka.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            jmeno TEXT NOT NULL,
            typ TEXT NOT NULL, 
            duvod TEXT,
            cas TIMESTAMP DEFAULT (datetime('now', 'localtime'))
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS pending_qr (
            token_uuid TEXT PRIMARY KEY,
            jmeno TEXT NOT NULL,
            typ TEXT NOT NULL,
            duvod TEXT,
            cas_vytvoreni TIMESTAMP DEFAULT (datetime('now', 'localtime')),
            pouzito BOOLEAN DEFAULT 0
        )
    ''')
    conn.commit()
    
    # Zajištění migrace pro existující DB
    for table, col, default in [('log', 'duvod', ''), ('pending_qr', 'typ', '"Odchod"')]:
        try:
            c.execute(f'ALTER TABLE {table} ADD COLUMN {col} TEXT DEFAULT {default}')
            conn.commit()
        except sqlite3.OperationalError:
            pass # Sloupec již existuje
            
    conn.close()

# --- KIOSK (Fyzická čtečka) ---
@app.route('/')
def index():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT jmeno, typ, duvod, cas FROM log ORDER BY id DESC LIMIT 15')
    zaznamy = c.fetchall()
    conn.close()
    return render_template('index.html', zaznamy=zaznamy)

@app.route('/scan', methods=['POST'])
def scan():
    qr_data = request.form.get('qr_data', '').strip()
    if not qr_data:
        return redirect(url_for('index'))
    
    # Ošetření vstupu z čtečky simulující US klávesnici na českém systému
    cz_to_en = str.maketrans("+ěščřžýáíé=", "1234567890-")
    qr_data = qr_data.translate(cz_to_en)
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    jmeno = qr_data
    duvod = ""
    typ = "Příchod"
    
    if len(qr_data) == 36:
        # Jedná se o vygenerovaný UUID token z mobilu
        c.execute('SELECT jmeno, typ, duvod, pouzito FROM pending_qr WHERE token_uuid = ?', (qr_data,))
        pending = c.fetchone()
        if pending and pending[3] == 0:
            jmeno = pending[0]
            typ = pending[1]
            duvod = pending[2] if pending[2] else ""
            c.execute('UPDATE pending_qr SET pouzito = 1 WHERE token_uuid = ?', (qr_data,))
        else:
            conn.close()
            return redirect(url_for('index')) # Neplatný nebo použitý QR kód
    else:
        # Běžné odpípnutí samotného jména - střídáme stav
        c.execute('SELECT typ FROM log WHERE jmeno = ? ORDER BY id DESC LIMIT 1', (jmeno,))
        last_record = c.fetchone()
        if last_record and last_record[0] == 'Příchod':
            typ = 'Odchod'
            
    c.execute('INSERT INTO log (jmeno, typ, duvod) VALUES (?, ?, ?)', (jmeno, typ, duvod))
    conn.commit()
    conn.close()
    
    return redirect(url_for('index'))

# --- MOBILNÍ GENERÁTOR ---
@app.route('/mobil')
def mobil():
    return render_template('mobil.html', qr_b64=None)

@app.route('/generovat', methods=['POST'])
def generovat():
    jmeno = request.form.get('jmeno', '').strip()
    typ = request.form.get('typ', 'Odchod').strip()
    duvod = request.form.get('duvod', '').strip()
    
    if not jmeno:
        return redirect(url_for('mobil'))
        
    # Pokud se vrací zvenku, důvod nepotřebujeme
    if typ == 'Příchod':
        duvod = ''

    token = str(uuid.uuid4())
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('INSERT INTO pending_qr (token_uuid, jmeno, typ, duvod) VALUES (?, ?, ?, ?)', (token, jmeno, typ, duvod))
    conn.commit()
    conn.close()

    # Tvorba QR kódu do Base64
    qr = qrcode.QRCode(version=1, box_size=8, border=4)
    qr.add_data(token)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    qr_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')

    return render_template('mobil.html', jmeno=jmeno, typ=typ, duvod=duvod, qr_b64=qr_b64)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)