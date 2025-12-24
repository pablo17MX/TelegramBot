import sqlite3

db = sqlite3.connect("database.db")
c = db.cursor()

contenidos = [

    # 🎬 PELÍCULAS
    (
        "Ted (2012)",
        "pelicula",
        None,
        "AgACAgEAAxkBAAMaaUtenVxa7fc93oqI_080wnnqZNsAAi6tMRu8BzBFGLlHQ7VZlhUBAAMCAAN4AAM2BA",
        "BAACAgEAAxkBAAMcaUte2DiTex9jQbxVS1redi5dCCQAAuAGAALL1lBHSdhVn-txq8w2BA"
    ),

    (
        "El Señor de los Anillos",
        "pelicula",
        None,
        "AGACAgQAAxkBAAIBXYZ_FOTO_ID",
        "BAACAgQAAxkBAAIBXYZ_VIDEO_ID"
    ),

    # 📺 SERIES
    (
        "Academia de Golf (2024)",
        "serie",
        "https://t.me/c/2786719679/1063",
        None,
        None
    )
]

c.executemany("""
    INSERT INTO contenidos (titulo, tipo, enlace, foto_id, video_id)
    VALUES (?, ?, ?, ?, ?)
""", contenidos)

db.commit()
db.close()

print("✅ Contenido cargado correctamente")
