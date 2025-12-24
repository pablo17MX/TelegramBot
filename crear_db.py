import sqlite3

db = sqlite3.connect("database.db")
c = db.cursor()

# CONTENIDOS
c.execute("""
CREATE TABLE IF NOT EXISTS contenidos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT,
    tipo TEXT,
    enlace TEXT,
    foto_id TEXT,
    video_id TEXT
)
""")

# WATCHLIST
c.execute("""
CREATE TABLE IF NOT EXISTS watchlist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    titulo TEXT,
    UNIQUE(user_id, titulo)
)
""")

# PETICIONES DESDE GRUPO
c.execute("""
CREATE TABLE IF NOT EXISTS solicitudes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    username TEXT,
    titulo TEXT,
    estado TEXT DEFAULT 'pendiente'
)
""")

# TOP DE BÚSQUEDAS
c.execute("""
CREATE TABLE IF NOT EXISTS busquedas (
    texto TEXT PRIMARY KEY,
    contador INTEGER DEFAULT 1
)
""")

db.commit()
db.close()

print("✅ Base de datos lista")
