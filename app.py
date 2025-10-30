from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import mysql.connector
import pickle
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta'

# ========================
#   CONFIGURACIÓN GENERAL
# ========================
app.static_folder = 'static'
app.template_folder = 'templates'

# Conexión a MySQL
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # Agrega tu contraseña si la tienes
    'database': 'chatbot'
}

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

# ========================
#   DECORADOR LOGIN REQUERIDO
# ========================
def login_requerido(f):
    @wraps(f)
    def verificar(*args, **kwargs):
        if 'usuario' not in session or not session['usuario']:
            flash("⚠️ Debes iniciar sesión para acceder al chat.")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return verificar

# ========================
#   CARGAR MODELO DE IA
# ========================
MODEL_PATH = os.path.join('models', 'modelo_logistico.pkl')
VEC_PATH = os.path.join('models', 'vectorizador.pkl')

modelo = None
vectorizador = None

if os.path.exists(MODEL_PATH) and os.path.exists(VEC_PATH):
    with open(MODEL_PATH, 'rb') as f:
        modelo = pickle.load(f)
    with open(VEC_PATH, 'rb') as f:
        vectorizador = pickle.load(f)
    print("✅ Modelo y vectorizador cargados correctamente.")
else:
    print("⚠️ No se encontraron modelo/vectorizador. El chatbot funcionará en modo básico.")

# ========================
#   RUTAS PÚBLICAS
# ========================
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/services')
def services():
    return render_template('service.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

# ========================
#   REGISTRO DE USUARIOS
# ========================
@app.route('/register', methods=['GET', 'POST'])
def register():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        cur.execute("SELECT * FROM users WHERE username = %s OR email = %s", (username, email))
        existing_user = cur.fetchone()

        if existing_user:
            flash("⚠️ El usuario o correo ya está registrado.")
            return redirect(url_for('register'))

        cur.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                    (username, email, password))
        conn.commit()
        flash("🎈 ¡Registro exitoso! Ahora puedes iniciar sesión.")
        return redirect(url_for('login'))

    cur.close()
    conn.close()
    return render_template('register.html')

# ========================
#   LOGIN / LOGOUT
# ========================
@app.route('/login', methods=['GET', 'POST'])
def login():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cur.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
        user = cur.fetchone()

        if user:
            session['usuario'] = username
            flash(f"🎉 Bienvenido, {username}.")
            return redirect(url_for('principal'))
        else:
            flash("⚠️ Usuario o contraseña incorrectos.")
            return redirect(url_for('login'))

    cur.close()
    conn.close()
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    flash("👋 Has cerrado sesión.")
    return redirect(url_for('login'))

# ========================
#   SECCIONES PROTEGIDAS
# ========================
@app.route('/principal')
@login_requerido
def principal():
    return render_template('principal.html', usuario=session['usuario'])

# ========================
#   CHATBOT (ÚNICA FUNCIÓN)
# ========================
@app.route('/procesar_chat', methods=['POST'])
@login_requerido
def procesar_chat():
    try:
        data = request.get_json()
        emocion = data.get('emocion', '').lower()
        motivo = data.get('motivo', '')
        influencia_entorno = data.get('influencia_entorno', '')
        frecuencia = data.get('frecuencia', '')
        concentracion = data.get('concentracion', '')
        energia = data.get('energia', '')
        sueno = data.get('sueno', '')

        # === Análisis simple ===
        if "triste" in emocion or "estres" in emocion or "cansado" in emocion:
            resultado_ml = "Estado emocional negativo"
            recomendacion = "Tómate un descanso y realiza alguna actividad que disfrutes. 💬"
        elif "feliz" in emocion or "alegre" in emocion or "motivado" in emocion:
            resultado_ml = "Estado emocional positivo"
            recomendacion = "Sigue manteniendo esa energía positiva durante el día. 🌞"
        else:
            resultado_ml = "Estado emocional neutro"
            recomendacion = "Reflexiona sobre tus emociones para entender mejor tu estado. 🤍"

        # === Guardar en MySQL ===
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',
            database='chatbot'
        )
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO respuestas_chat 
            (nombre, emocion_reportada, motivo, influencia_entorno, frecuencia, 
             concentracion, energia, sueno, resultado_ml, recomendacion, fecha)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """, (
            session['usuario'], 
            emocion,
            motivo,
            influencia_entorno,
            frecuencia,
            concentracion,
            energia,
            sueno,
            resultado_ml,
            recomendacion
        ))
        conn.commit()
        cur.close()
        conn.close()

        print("✅ Registro guardado correctamente en respuestas_chat.")

        return jsonify({
            "resultado": resultado_ml,
            "recomendacion": recomendacion
        })

    except Exception as e:
        import traceback
        print("❌ Error en procesar_chat:", e)
        print(traceback.format_exc())
        return jsonify({"error": "Error al procesar los datos"}), 500

# ========================
#   OTRAS SECCIONES
# ========================
@app.route('/entendimiento-negocio')
@login_requerido
def entendimiento_negocio():
    return render_template('entendimiento_negocio.html', usuario=session['usuario'])

@app.route('/ingenieria-datos')
@login_requerido
def ingenieria_datos():
    return render_template('ingenieria_datos.html', usuario=session['usuario'])

@app.route('/introduccion')
@login_requerido
def introduccion():
    return render_template('introduccion.html', usuario=session['usuario'])

@app.route('/objetivos')
@login_requerido
def objetivos():
    return render_template('objetivos.html', usuario=session['usuario'])

@app.route('/descripcion')
@login_requerido
def descripcion():
    return render_template('descripcion.html', usuario=session['usuario'])

# ========================
#   CHAT VIEW
# ========================
@app.route('/chat')
@login_requerido
def chat():
    return render_template('chats.html', usuario=session['usuario'])

# ========================
#   EJECUCIÓN DEL SERVIDOR
# ========================
if __name__ == '__main__':
    app.run(debug=True)
