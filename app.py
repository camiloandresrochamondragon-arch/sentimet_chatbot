from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta'

# Conexión a SQLite
db = sqlite3.connect('chatbot.db', check_same_thread=False)
cursor = db.cursor()

# Crear tabla si no existe
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        email TEXT NOT NULL,
        password TEXT NOT NULL
    )
''')
db.commit()

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()

        if user:
            session['usuario'] = username
            flash(f"🎉 Bienvenido de nuevo, {username}.")
            return redirect(url_for('inicio'))
        else:
            flash("⚠️ Usuario o contraseña incorrectos. Intenta de nuevo.")
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        cursor.execute("SELECT * FROM users WHERE username = ? OR email = ?", (username, email))
        existing_user = cursor.fetchone()

        if existing_user:
            flash("⚠️ El usuario o correo ya está registrado. Intenta con otros datos.")
            return redirect(url_for('register'))

        cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                       (username, email, password))
        db.commit()
        flash("🎈 ¡Registro exitoso! Ahora puedes iniciar sesión.")
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/inicio')
def inicio():
    if 'usuario' in session:
        usuario = session['usuario']
        return render_template('index.html', usuario=usuario)
    else:
        flash("⚠️ Debes iniciar sesión para acceder a la plataforma.")
        return redirect(url_for('login'))

@app.route('/chat')
def chat():
    if 'usuario' in session:
        usuario = session['usuario']
        return render_template('chats.html', usuario=usuario)
    else:
        flash("⚠️ Debes iniciar sesión para acceder al chat.")
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('login'))

@app.route('/introduccion')
def introduccion():
    if 'usuario' in session:
        usuario = session['usuario']
        return render_template('introduccion.html', usuario=usuario)
    else:
        flash("⚠️ Debes iniciar sesión para acceder a esta sección.")
        return redirect(url_for('login'))

@app.route('/objetivos')
def objetivos():
    if 'usuario' in session:
        usuario = session['usuario']
        return render_template('objetivos.html', usuario=usuario)
    else:
        flash("⚠️ Debes iniciar sesión para acceder a esta sección.")
        return redirect(url_for('login'))

@app.route('/descripcion')
def descripcion():
    if 'usuario' in session:
        usuario = session['usuario']
        return render_template('descripcion.html', usuario=usuario)
    else:
        flash("⚠️ Debes iniciar sesión para acceder a esta sección.")
        return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)