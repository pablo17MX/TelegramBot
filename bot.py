import os
import sqlite3
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# =========================
# CONFIGURACIÓN
# =========================
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("❌ BOT_TOKEN no está definido")

ADMIN_ID = 1362881076
WELCOME_IMAGE_ID = "AgACAgEAAxkBAANsaUuAT63j9InZTN50PrKBTIv29EMAAkgLaxsZRFlGtN5Q-bc8GBsBAAMCAAN5AAM2BA"

DB_NAME = "database.db"

# =========================
# BASE DE DATOS
# =========================
def conectar():
    return sqlite3.connect(DB_NAME)

# =========================
# ESTADOS TEMPORALES
# =========================
estado_carga = {}
estado_edicion = {}

# =========================
# REGISTRAR BÚSQUEDA
# =========================
def registrar_busqueda(texto):
    db = conectar()
    c = db.cursor()

    c.execute("SELECT contador FROM busquedas WHERE texto=?", (texto,))
    fila = c.fetchone()

    if fila:
        c.execute("UPDATE busquedas SET contador=contador+1 WHERE texto=?", (texto,))
    else:
        c.execute("INSERT INTO busquedas (texto, contador) VALUES (?,1)", (texto,))

    db.commit()
    db.close()

# =========================
# BIENVENIDA AL GRUPO
# =========================
async def bienvenida(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for user in update.message.new_chat_members:
        texto = (
            f"👋 *Bienvenido {user.first_name}*\n\n"
            f"🎬 Grupo: *{update.effective_chat.title}*\n\n"
            "📌 Usa *#peticion* para solicitar contenido\n"
            "🔍 /buscar para ver películas y series\n"
            "⭐ Guarda contenido en tu lista\n\n"
            "¡Disfruta! 🍿"
        )

        await update.message.reply_photo(
            photo=WELCOME_IMAGE_ID,
            caption=texto,
            parse_mode="Markdown"
        )

# =========================
# /start
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 *Bienvenido*\n\n"
        "/buscar nombre\n"
        "/milista\n"
        "/peticion\n"
        "/top",
        parse_mode="Markdown"
    )

# =========================
# /buscar
# =========================
async def buscar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Usa: /buscar nombre")
        return

    texto = " ".join(context.args)
    registrar_busqueda(texto.lower())

    db = conectar()
    c = db.cursor()
    c.execute("""
        SELECT titulo, tipo, enlace, foto_id, video_id
        FROM contenidos
        WHERE titulo LIKE ?
    """, (f"%{texto}%",))
    resultados = c.fetchall()
    db.close()

    if not resultados:
        await update.message.reply_text("❌ No encontrado. Usa /peticion")
        return

    for titulo, tipo, enlace, foto_id, video_id in resultados:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Agregar a mi lista", callback_data=f"add:{titulo}")]
        ])

        if tipo == "pelicula":
            await update.message.reply_photo(photo=foto_id, caption=f"🎬 {titulo}")
            await update.message.reply_video(video=video_id, reply_markup=keyboard)
        else:
            await update.message.reply_text(f"📺 {titulo}\n\n🔗 {enlace}", reply_markup=keyboard)

# =========================
# /top
# =========================
async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = conectar()
    c = db.cursor()
    c.execute("SELECT texto, contador FROM busquedas ORDER BY contador DESC LIMIT 10")
    datos = c.fetchall()
    db.close()

    if not datos:
        await update.message.reply_text("📊 Aún no hay búsquedas")
        return

    msg = "🔥 *Top más buscados*\n\n"
    for i, (texto, contador) in enumerate(datos, 1):
        msg += f"{i}. {texto} — {contador}\n"

    await update.message.reply_text(msg, parse_mode="Markdown")

# =========================
# /peticion
# =========================
async def peticion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📩 *Las peticiones se hacen en el grupo*\n\n"
        "Formato:\n"
        "#peticion\n"
        "📸 Foto\n"
        "🎬 Nombre\n"
        "📺 Tipo\n"
        "📅 Año",
        parse_mode="Markdown"
    )

# =========================
# /milista
# =========================
async def milista(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = conectar()
    c = db.cursor()
    c.execute("SELECT titulo FROM watchlist WHERE user_id=?", (update.effective_user.id,))
    datos = c.fetchall()
    db.close()

    if not datos:
        await update.message.reply_text("📭 Tu lista está vacía")
        return

    texto = "⭐ *Mi Lista*\n\n"
    for (titulo,) in datos:
        texto += f"• {titulo}\n"

    await update.message.reply_text(texto, parse_mode="Markdown")

# =========================
# CALLBACK ➕ AGREGAR A LISTA
# =========================
async def agregar_lista(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    titulo = query.data.replace("add:", "")
    user_id = query.from_user.id

    db = conectar()
    db.execute(
        "INSERT OR IGNORE INTO watchlist (user_id, titulo) VALUES (?,?)",
        (user_id, titulo)
    )
    db.commit()
    db.close()

    await query.edit_message_reply_markup(reply_markup=None)
    await query.message.reply_text("⭐ Agregado a tu lista")

# =========================
# CAPTURAR #peticion EN GRUPO
# =========================
async def detectar_peticion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "#peticion" not in update.message.text.lower():
        return

    db = conectar()
    db.execute(
        "INSERT INTO solicitudes (user_id, titulo, estado) VALUES (?,?, 'pendiente')",
        (update.effective_user.id, update.message.text[:200])
    )
    db.commit()
    db.close()

# =========================
# MAIN
# =========================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("buscar", buscar))
    app.add_handler(CommandHandler("top", top))
    app.add_handler(CommandHandler("peticion", peticion))
    app.add_handler(CommandHandler("milista", milista))

    app.add_handler(CallbackQueryHandler(agregar_lista))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, bienvenida))
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, detectar_peticion))

    print("🤖 Bot iniciado correctamente")
    app.run_polling()

if __name__ == "__main__":
    main()
