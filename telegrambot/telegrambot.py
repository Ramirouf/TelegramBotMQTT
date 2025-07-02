from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler, ConversationHandler
import logging, os, asyncio, aiomqtt, ssl
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
token=os.environ["TB_TOKEN"]
autorizados=[int(x) for x in os.environ["TB_AUTORIZADOS"].split(',')]
MQTT_TOPIC_PREFIX = "6553C66F88E0CD81"

logging.basicConfig(format='%(asctime)s - TelegramBot - %(levelname)s - %(message)s', level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING) # Sólo mostrar si es warning o superior. No mostrará los INFO HTTP OK

# --- Conversation States ---
SETPOINT, PERIODO = range(2)

# --- MQTT Publishing Function ---
async def publish_mqtt(context: ContextTypes.DEFAULT_TYPE, subtopic: str, payload: str):
    try:
        client = context.bot_data['mqtt_client']
        topic = f"{MQTT_TOPIC_PREFIX}/{subtopic}"
        await client.publish(topic, payload)
        logging.info(f"Published to {topic}: {payload}")
        return True
    except Exception as e:
        logging.error(f"Failed to publish to MQTT: {e}")
        return False

# --- Main Menu ---
async def get_main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("🌡️ Setpoint", callback_data='setpoint')],
        [InlineKeyboardButton("⏰ Periodo", callback_data='periodo')],
        [InlineKeyboardButton("💡 Destello", callback_data='destello')],
        [InlineKeyboardButton("⚙️ Modo", callback_data='modo')],
        [InlineKeyboardButton("⚡ Relé", callback_data='rele')],
    ]
    return InlineKeyboardMarkup(keyboard)

async def sin_autorizacion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("intento de conexión de: " + str(update.message.from_user.id))
    await context.bot.send_message(chat_id=update.effective_chat.id, text="No autorizado")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(update)
    logging.info(f"se conectó: {str(update.message.from_user.id)} {update.message.from_user.first_name} {update.message.from_user.last_name}")
    if update.message.from_user.first_name:
        nombre=update.message.from_user.first_name
    else:
        nombre=""
    if update.message.from_user.last_name:
        apellido=update.message.from_user.last_name
    else:
        apellido=""
    await context.bot.send_message(update.message.chat.id, text="Bienvenido, "+ nombre + " " + apellido)
    reply_markup = await get_main_menu_keyboard()
    await update.message.reply_text(
        f"Seleccione una opción para controlar el termostato:",
        reply_markup=reply_markup
    )
    # await update.message.reply_text("Bienvenido al Bot "+ nombre + " " + apellido) # también funciona

async def acercade(update: Update, context):
    await context.bot.send_message(update.message.chat.id, text="Este bot permite modificar los parámetros de setpoint, periodo, destello, modo y relé")

async def setpoint(update: Update, context):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="Enviar el nuevo setpoint en °C sin decimal (entre -20 y 100):")
    return SETPOINT

async def setpoint_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        setpoint_value = int(update.message.text)
        if -20 <= setpoint_value <= 100:
            if await publish_mqtt(context, 'setpoint', str(setpoint_value)):
                await update.message.reply_text(f"✅ Periodo actualizado a: {setpoint_value} segundos.")
                reply_markup = await get_main_menu_keyboard()
                await update.message.reply_text("Selecciona otra opción:", reply_markup=reply_markup)
            else:
                await update.message.reply_text("❌ Error al enviar el valor a MQTT.")
            return ConversationHandler.END
        else:
            await update.message.reply_text("El periodo debe ser un número positivo. Inténtalo de nuevo.")
            return PERIODO
    except ValueError:
        await update.message.reply_text("Entrada inválida. Por favor, envía solo un número entero.")
        return PERIODO

async def modo(update: Update, context):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("🤖 Modo Automático", callback_data='modo_auto')],
        [InlineKeyboardButton("🕹️ Modo Manual", callback_data='modo_manual')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text="Seleccione el modo de operación:", reply_markup=reply_markup)

async def modo_auto(update: Update, context):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text=f"Selected option: {query.data}")
    if await publish_mqtt(context, 'modo', '0'):
         await query.edit_message_text("✅ Modo automático activado.", reply_markup=await get_main_menu_keyboard())
    else:
        await query.edit_message_text("❌ Error al activar el modo automático.", reply_markup=await get_main_menu_keyboard())

async def modo_manual(update: Update, context):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text=f"Selected option: {query.data}")
    if await publish_mqtt(context, 'modo', '1'):
         await query.edit_message_text("✅ Modo manual activado.", reply_markup=await get_main_menu_keyboard())
    else:
        await query.edit_message_text("❌ Error al activar el modo manual.", reply_markup=await get_main_menu_keyboard())

async def destello(update: Update, context):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text=f"Selected option: {query.data}")
    if await publish_mqtt(context, 'destello', '1'):
         await query.edit_message_text("💡✨ ¡Destello enviado!", reply_markup=await get_main_menu_keyboard())
    else:
        await query.edit_message_text("❌ Error al enviar la orden de destello.", reply_markup=await get_main_menu_keyboard())

async def rele(update: Update, context):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("🔴 Encender Relé", callback_data='rele_on')],
        [InlineKeyboardButton("⚫ Apagar Relé", callback_data='rele_off')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text="Seleccione una opción para el relé:", reply_markup=reply_markup)

async def rele_on(update: Update, context):
    query = update.callback_query
    await query.answer()
    if await publish_mqtt(context, 'rele', '1'):
         await query.edit_message_text("🔴 Relé encendido.", reply_markup=await get_main_menu_keyboard())
    else:
        await query.edit_message_text("❌ Error al encender el relé.", reply_markup=await get_main_menu_keyboard())

async def rele_off(update: Update, context):
    query = update.callback_query
    await query.answer()
    if await publish_mqtt(context, 'rele', '0'):
         await query.edit_message_text("⚫ Relé apagado.", reply_markup=await get_main_menu_keyboard())
    else:
        await query.edit_message_text("❌ Error al apagar el relé.", reply_markup=await get_main_menu_keyboard())

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Operación cancelada.", reply_markup=await get_main_menu_keyboard()
    )
    return ConversationHandler.END


async def main():
    # TLS setup for mqtts
    tls_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    tls_context.verify_mode = ssl.CERT_REQUIRED
    tls_context.check_hostname = True
    tls_context.load_default_certs()

    # Connect to MQTT broker
    async with aiomqtt.Client(os.environ['SERVIDOR'], port=23816, username=os.environ['MQTT_USR'],password=os.environ['MQTT_PASS'] ,tls_context=tls_context) as client:
        await client.publish("test", "Conectado al broker MQTT")
    
        logging.info(autorizados)
        application = Application.builder().token(token).build()
        application.add_handler(MessageHandler((~filters.User(autorizados)), sin_autorizacion))
        application.add_handler(CommandHandler('start', start))
        application.add_handler(CommandHandler('acercade', acercade))
         # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", start)],
            states={
                    SETPOINT: [MessageHandler(filters.TEXT & ~filters.COMMAND, setpoint_receive)],
            },
            fallbacks=[CommandHandler('cancel', cancel)],
        )
        application.add_handler(conv_handler)
        
        application.add_handler(CallbackQueryHandler(modo, pattern='^modo$'))
        application.add_handler(CallbackQueryHandler(destello, pattern='^destello$'))
        application.add_handler(CallbackQueryHandler(modo_auto, pattern='^modo_auto$'))
        application.add_handler(CallbackQueryHandler(modo_manual, pattern='^modo_manual$'))
        application.add_handler(CallbackQueryHandler(setpoint, pattern='^setpoint$'))
        application.add_handler(CallbackQueryHandler(rele, pattern='^rele$'))
        application.add_handler(CallbackQueryHandler(rele_on, pattern='^rele_on$'))
        application.add_handler(CallbackQueryHandler(rele_off, pattern='^rele_off$'))

        application.bot_data['mqtt_client'] = client

        async with application:
            await application.start()
            await application.updater.start_polling()
            while True:
                try:
                    await asyncio.sleep(1)
                except Exception:
                    await application.updater.stop()
                    await application.stop()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Received Ctrl+C, shutting down...")