import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    filters
)
import sqlite3

# -------------------------
# CONFIGURACIÓN
# -------------------------
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("❌ BOT_TOKEN no está definido en las variables de entorno")

ADMIN_ID = 1362881076
WELCOME_IMAGE_ID = "AgACAgEAAxkBAANsaUuAT63j9InZTN50PrKBTIv29EMAAkgLaxsZRFlGtN5Q-bc8GBsBAAMCAAN5AAM2BA"

# -------------------------
# Conexión a la base de datos
# -------------------------
def conectar():
    return sqlite3.connect("database.db")

# -------------------------
# Estados temporales
# -------------------------
estado_carga = {}
estado_edicion = {}

# -------------------------
# REGISTRAR BÚSQUEDA
# -------------------------
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

# -------------------------
# Bienvenida
# -------------------------
async def bienvenida(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for user in update.message.new_chat_members:
        nombre = user.first_name
        grupo = update.effective_chat.title

        texto = (
            f"👋 *Bienvenido {nombre}*\n\n"
            f"🎬 Has entrado a *{grupo}*\n\n"
            "📌 Usa el hashtag *#peticion* para solicitar contenido\n"
            "🔍 Usa el bot para buscar películas y series\n"
            "⭐ Guarda contenido en tu lista personal\n\n"
            "¡Disfruta del grupo! 🍿"
        )

        await update.message.reply_photo(
            photo=WELCOME_IMAGE_ID,
            caption=texto,
            parse_mode="Markdown"
        )

# -------------------------
# Notificar Solicitud Cumplida
# -------------------------
async def notificar_peticion_cumplida(app, titulo):
    db = conectar()
    c = db.cursor()

    c.execute("""
        SELECT user_id
        FROM solicitudes
        WHERE titulo LIKE ?
        AND estado='pendiente'
    """, (f"%{titulo}%",))

    usuarios = c.fetchall()

    if usuarios:
        c.execute("""
            UPDATE solicitudes
            SET estado='cumplida'
            WHERE titulo LIKE ?
        """, (f"%{titulo}%",))
        db.commit()

    db.close()

    for (user_id,) in usuarios:
        try:
            await app.bot.send_message(
                chat_id=user_id,
                text=(
                    "🎉 *Tu petición fue cumplida*\n\n"
                    f"🎬 *{titulo}* ya está disponible.\n\n"
                    "🔍 Usa /buscar para verla\n"
                    "🍿 ¡Disfrútala!"
                ),
                parse_mode="Markdown"
            )
        except:
            pass

# -------------------------
# /start
# -------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 Bienvenido\n\n"
        "Comandos disponibles:\n"
        "/buscar nombre\n"
        "/peticion\n"
        "/milista"
    )

# -------------------------
# /buscar
# -------------------------
async def buscar(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:
        await update.message.reply_text("❌ Usa: /buscar nombre")
        return

    texto = " ".join(context.args)

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
            [InlineKeyboardButton("➕ Agregar a mi lista", callback_data=f"addlist:{titulo}")]
        ])

        # 🎬 PELÍCULA
        if tipo == "pelicula":
            await update.message.reply_photo(
                photo=foto_id,
                caption=f"🎬 {titulo}"
            )
            await update.message.reply_video(
                video=video_id,
                reply_markup=keyboard
            )

        # 📺 SERIE
        elif tipo == "serie":
            await update.message.reply_text(
                f"📺 {titulo}\n\n🔗 {enlace}",
                reply_markup=keyboard
            )

# -------------------------
# /top
# -------------------------
async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = conectar()
    c = db.cursor()
    c.execute("""
        SELECT texto, contador
        FROM busquedas
        ORDER BY contador DESC
        LIMIT 10
    """)
    datos = c.fetchall()
    db.close()

    if not datos:
        await update.message.reply_text("📊 Aún no hay búsquedas")
        return

    msg = "🔥 *Top más buscados*\n\n"
    for i, (texto, contador) in enumerate(datos, 1):
        msg += f"{i}️⃣ {texto} — {contador}\n"

    await update.message.reply_text(msg, parse_mode="Markdown")

# -------------------------
# /peticion
# -------------------------
async def peticion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📩 *Las solicitudes se hacen en el grupo oficial*\n\n"
        "👥 Grupo de peticiones:\n"
        "👉 https://t.me/CinemaTVPlus_Chat\n\n"
        "📝 Formato obligatorio:\n"
        "📸 Foto\n"
        "🎬 Nombre\n"
        "📺 Tipo (película / serie)\n"
        "📅 Año",
    )

# -------------------------
# /milista
# -------------------------
async def milista(update: Update, context: ContextTypes.DEFAULT_TYPE):

    db = conectar()
    c = db.cursor()
    c.execute(
        "SELECT titulo FROM watchlist WHERE user_id=?",
        (update.effective_user.id,)
    )
    lista = c.fetchall()
    db.close()

    if not lista:
        await update.message.reply_text("📭 Tu watchlist está vacía")
        return

    texto = "⭐ *Mi Lista:*\n\n"
    for (titulo,) in lista:
        texto += f"• {titulo}\n"

    await update.message.reply_text(texto, parse_mode="Markdown")

# -------------------------
# BOTÓN ➕ AGREGAR A MI LISTA
# -------------------------
async def agregar_a_lista(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    titulo = query.data.split("addlist:")[1]
    user_id = query.from_user.id

    db = conectar()
    db.execute(
        "INSERT OR IGNORE INTO watchlist (user_id, titulo) VALUES (?, ?)",
        (user_id, titulo)
    )
    db.commit()
    db.close()

    await query.edit_message_reply_markup(reply_markup=None)
    await query.message.reply_text("⭐ Agregado a tu lista")

# -------------------------
# /addpelicula (ADMIN)
# -------------------------
async def addpelicula(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    titulo = " ".join(context.args)
    if not titulo:
        await update.message.reply_text("❌ Usa: /addpelicula Título")
        return

    estado_carga[update.effective_user.id] = {
        "titulo": titulo,
        "tipo": "pelicula",
        "foto_id": None,
        "video_id": None,
        "modo": "nuevo"
    }

    await update.message.reply_text(
        "🎬 Película iniciada\n\n"
        "📸 Envía la FOTO con la descripción"
    )

# -------------------------
# /addserie (ADMIN)
# -------------------------
async def addserie(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    titulo = " ".join(context.args)
    if not titulo:
        await update.message.reply_text("❌ Usa: /addserie Título")
        return

    estado_carga[update.effective_user.id] = {
        "titulo": titulo,
        "tipo": "serie",
        "modo": "nuevo"
    }

    await update.message.reply_text("🔗 Envía el ENLACE de la serie")

# -------------------------
# /editar (ADMIN)
# -------------------------
async def editar(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    texto = " ".join(context.args)
    if not texto:
        await update.message.reply_text("❌ Usa: /editar nombre")
        return

    db = conectar()
    c = db.cursor()
    c.execute("""
        SELECT id, titulo, tipo
        FROM contenidos
        WHERE titulo LIKE ?
    """, (f"%{texto}%",))
    resultados = c.fetchall()
    db.close()

    if not resultados:
        await update.message.reply_text("❌ No se encontró contenido")
        return

    estado_edicion[update.effective_user.id] = resultados

    msg = "📋 Resultados:\n\n"
    for i, (_, titulo, tipo) in enumerate(resultados, 1):
        msg += f"{i}️⃣ {titulo} [{tipo}]\n"

    msg += "\n✏️ Responde:\n"
    msg += "`editar 1`\n"
    msg += "`eliminar 2`"

    await update.message.reply_text(msg, parse_mode="Markdown")

# -------------------------
# CAPTURAR MENSAJES (ADMIN)
# -------------------------
async def capturar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # ----- EDITAR / ELIMINAR -----
    if user_id in estado_edicion and update.message.text:
        partes = update.message.text.lower().split()
        if len(partes) != 2 or not partes[1].isdigit():
            return

        accion, idx = partes
        idx = int(idx) - 1
        lista = estado_edicion[user_id]

        if idx < 0 or idx >= len(lista):
            await update.message.reply_text("❌ Número inválido")
            return

        contenido_id, titulo, tipo = lista[idx]

        if accion == "eliminar":
            db = conectar()
            db.execute("DELETE FROM contenidos WHERE id=?", (contenido_id,))
            db.commit()
            db.close()
            del estado_edicion[user_id]
            await update.message.reply_text(f"🗑 Eliminado: {titulo}")
            return

        if accion == "editar":
            estado_carga[user_id] = {
                "id": contenido_id,
                "titulo": titulo,
                "tipo": tipo,
                "foto_id": None,
                "video_id": None,
                "modo": "editar"
            }
            del estado_edicion[user_id]

            await update.message.reply_text(
                "📸 Envía la NUEVA FOTO" if tipo == "pelicula" else "🔗 Envía el NUEVO ENLACE"
            )
            return

    # ----- CARGA / EDICIÓN -----
    if user_id not in estado_carga:
        return

    data = estado_carga[user_id]

    # 🎬 PELÍCULA
    if data["tipo"] == "pelicula":

        if update.message.photo and not data["foto_id"]:
            data["foto_id"] = update.message.photo[-1].file_id
            await update.message.reply_text("🎥 Ahora envía el VIDEO")
            return

        if update.message.video and not data["video_id"]:
            data["video_id"] = update.message.video.file_id

            db = conectar()
            if data["modo"] == "editar":
                db.execute("""
                    UPDATE contenidos
                    SET foto_id=?, video_id=?
                    WHERE id=?
                """, (data["foto_id"], data["video_id"], data["id"]))
            else:
                db.execute("""
                    INSERT INTO contenidos (titulo, tipo, enlace, foto_id, video_id)
                    VALUES (?, 'pelicula', NULL, ?, ?)
                """, (data["titulo"], data["foto_id"], data["video_id"]))
            db.commit()
            db.close()

            del estado_carga[user_id]
            await notificar_peticion_cumplida(context.application, data["titulo"])
            await update.message.reply_text("✅ Película guardada y notificaciones enviadas")
            return

    # 📺 SERIE
    if data["tipo"] == "serie" and update.message.text:
        enlace = update.message.text.strip()

        db = conectar()
        if data["modo"] == "editar":
            db.execute("UPDATE contenidos SET enlace=? WHERE id=?", (enlace, data["id"]))
        else:
            db.execute("""
                INSERT INTO contenidos (titulo, tipo, enlace, foto_id, video_id)
                VALUES (?, 'serie', ?, NULL, NULL)
            """, (data["titulo"], enlace))
        db.commit()
        db.close()

        del estado_carga[user_id]
        await notificar_peticion_cumplida(context.application, data["titulo"])
        await update.message.reply_text("✅ Serie guardada y notificaciones enviadas")

# -------------------------
# MAIN
# -------------------------
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("buscar", buscar))
    app.add_handler(CommandHandler("peticion", peticion))
    app.add_handler(CommandHandler("milista", milista))
    app.add_handler(CommandHandler("addpelicula", addpelicula))
    app.add_handler(CommandHandler("addserie", addserie))
    app.add_handler(CommandHandler("editar", editar))
    app.add_handler(CommandHandler("top", top))

    app.add_handler(CallbackQueryHandler(agregar_a_lista))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, bienvenida))
    app.add_handler(MessageHandler(filters.ALL, capturar))

    print("🤖 Bot iniciado correctamente")
    app.run_polling()

if __name__ == "__main__":
    main()


