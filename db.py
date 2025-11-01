import psycopg2

conn = psycopg2.connect(
    host="dpg-d42mb0q4d50c739s5u30-a.oregon-postgres.render.com",
    database="chatbot_de_sentimet",
    user="chatbot_de_sentimet_user",
    password="NofcaUnhWwJPl2V2Md9dC4WojRbdWnrl",
    port="5432"
)

cursor = conn.cursor()
print("✅ Conexión exitosa a la base de datos PostgreSQL")
