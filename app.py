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
    'password': '',  # agrega tu contraseña si la tienes
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
#   PÁGINAS PÚBLICAS
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

@app.route('/politicas')
def politicas():
    return render_template('politicas.html')

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
#   📊 ESTADÍSTICAS DE EMOCIONES
# ========================
@app.route('/estadisticas_ml')
@login_requerido
def estadisticas_ml():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT emocion_reportada, resultado_ml
        FROM respuestas_chat
        WHERE nombre = %s
        AND emocion_reportada IS NOT NULL
        AND resultado_ml IS NOT NULL
    """, (session['usuario'],))
    datos = cur.fetchall()
    cur.close()
    conn.close()

    if not datos:
        return render_template("estadisticas_ml.html", etiquetas=None, reales=None, predichas=None)

    # Contar frecuencia de emociones reales y predichas
    from collections import Counter
    reales = Counter([d['emocion_reportada'].lower() for d in datos])
    predichas = Counter([d['resultado_ml'].lower() for d in datos])
    etiquetas = sorted(list(set(list(reales.keys()) + list(predichas.keys()))))

    reales_valores = [reales.get(e, 0) for e in etiquetas]
    predichas_valores = [predichas.get(e, 0) for e in etiquetas]

    return render_template('estadisticas_ml.html',
                           etiquetas=etiquetas,
                           reales=reales_valores,
                           predichas=predichas_valores)


@app.route('/estadisticas')
@login_requerido
def estadisticas():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT resultado_ml, COUNT(*) AS cantidad
        FROM respuestas_chat
        WHERE nombre = %s
        GROUP BY resultado_ml
    """, (session['usuario'],))
    datos = cur.fetchall()
    cur.close()
    conn.close()

    etiquetas = [d['resultado_ml'] for d in datos]
    valores = [d['cantidad'] for d in datos]

    return render_template('estadisticas.html',
                           usuario=session['usuario'],
                           etiquetas=etiquetas,
                           valores=valores)

@app.route('/evaluacion_modelo')
@login_requerido
def evaluacion_modelo():
    import matplotlib.pyplot as plt
    import io, base64
    import numpy as np
    from sklearn.metrics import confusion_matrix, accuracy_score

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT emocion_reportada, resultado_ml
        FROM respuestas_chat
        WHERE nombre = %s
        AND emocion_reportada IS NOT NULL
        AND resultado_ml IS NOT NULL
    """, (session['usuario'],))
    datos = cur.fetchall()
    cur.close()
    conn.close()

    if not datos:
        return render_template("evaluacion_modelo.html", imagen_base64=None, mensaje="Aún no hay datos suficientes para generar la matriz.")

    reales = [d['emocion_reportada'].lower() for d in datos]
    predichas = [d['resultado_ml'].lower() for d in datos]
    etiquetas = sorted(list(set(reales + predichas)))

    matriz = confusion_matrix(reales, predichas, labels=etiquetas)
    precision = accuracy_score(reales, predichas) * 100

    # === 🎨 ESTILO VISUAL MEJORADO ===
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(matriz, interpolation='nearest', cmap='Blues')

    # Barra de color
    cbar = ax.figure.colorbar(im, ax=ax)
    cbar.ax.set_ylabel("Frecuencia", rotation=-90, va="bottom")

    # Etiquetas
    ax.set(
        xticks=np.arange(len(etiquetas)),
        yticks=np.arange(len(etiquetas)),
        xticklabels=etiquetas,
        yticklabels=etiquetas,
        title="Matriz de Confusión (Datos del Usuario)",
        ylabel="Etiqueta Real",
        xlabel="Predicción del Modelo"
    )

    # Rotar etiquetas del eje X
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right", rotation_mode="anchor")

    # Valores dentro de cada celda
    thresh = matriz.max() / 2.
    for i in range(matriz.shape[0]):
        for j in range(matriz.shape[1]):
            ax.text(j, i, format(matriz[i, j], 'd'),
                    ha="center", va="center",
                    color="white" if matriz[i, j] > thresh else "black")

    fig.tight_layout()
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight')
    buffer.seek(0)
    imagen_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    buffer.close()
    plt.close(fig)

    return render_template("evaluacion_modelo.html", imagen_base64=imagen_base64, precision=precision, mensaje=None)

# ========================
#   CHATBOT PRINCIPAL
# ========================
@app.route('/chat')
def chat():
    return render_template('chats.html')

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
            resultado_ml = "Negativo"
            recomendacion = "Tómate un descanso y realiza alguna actividad que disfrutes. 💬"
        elif "feliz" in emocion or "alegre" in emocion or "motivado" in emocion:
            resultado_ml = "Positivo"
            recomendacion = "Sigue manteniendo esa energía positiva durante el día. 🌞"
        else:
            resultado_ml = "Neutro"
            recomendacion = "Reflexiona sobre tus emociones para entender mejor tu estado. 🤍"

        # === Guardar en MySQL ===
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO respuestas_chat 
            (nombre, emocion_reportada, resultado_ml, recomendacion, fecha)
            VALUES (%s, %s, %s, %s, NOW())
        """, (
            session['usuario'],
            emocion,
            resultado_ml,
            recomendacion
        ))
        conn.commit()
        cur.close()
        conn.close()

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
#   EJECUCIÓN DEL SERVIDOR
# ========================
if __name__ == '__main__':
    app.run(debug=True)
