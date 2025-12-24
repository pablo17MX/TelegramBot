import sqlite3

db = sqlite3.connect("database.db")
c = db.cursor()

c.execute("SELECT id, titulo, tipo FROM contenidos")
filas = c.fetchall()

for f in filas:
    print(f)

db.close()
