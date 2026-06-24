import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Токен бота (замените на свой)
BOT_TOKEN = "8908126962:AAEHJySFXe289oH3SXuYXdRgeaqEgvg7LWM"

# Текст правил
RULES_TEXT = """
📜 *ПРАВИЛА ЧАТА*

1. Будьте вежливы и уважайте других участников
2. Запрещён спам, реклама и провокации
3. Не используйте нецензурную лексику
4. Обсуждайте только темы, соответствующие тематике чата
5. Запрещена публикация личной информации без согласия

⚠️ Нарушение правил влечёт за собой предупреждение или блокировку.

Нажимая кнопку "Согласен", вы подтверждаете, что ознакомились с правилами и обязуетесь их соблюдать.
"""

# Обработчик новых участников
async def new_member_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Проверяем, есть ли новые участники
    for member in update.message.new_chat_members:
        # Пропускаем, если новый участник - сам бот
        if member.id == context.bot.id:
            continue
            
        keyboard = [
            [InlineKeyboardButton("✅ Согласен", callback_data=f'agree_{member.id}')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Отправляем правила новому участнику
        await update.message.reply_text(
            f"👋 Добро пожаловать, {member.first_name}!\n\n{RULES_TEXT}",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

# Обработчик нажатия на кнопку
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # Получаем ID пользователя из callback_data
    user_id = int(query.data.split('_')[1])
    
    # Проверяем, что кнопку нажимает тот же пользователь
    if query.from_user.id != user_id:
        await query.answer("❌ Эта кнопка не для вас!", show_alert=True)
        return
    
    await query.edit_message_text(
        f"✅ *Спасибо, {query.from_user.first_name}! Вы приняли правила.*\n\n"
        f"Теперь вы можете общаться в чате.",
        parse_mode='Markdown'
    )
    
    # Здесь можно добавить логику:
    # - Сохранить в базу данных, что пользователь согласился
    # - Выдать роль в группе
    # - И т.д.

# Обработчик команды /start (для личных сообщений)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Привет! Я бот для управления правилами группы.\n"
        "Добавьте меня в группу и сделайте администратором,\n"
        "и я буду автоматически приветствовать новых участников."
    )

# Основная функция
def main():
    # Создаём приложение
    application = Application.builder().token(BOT_TOKEN).build()

    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_member_handler))
    application.add_handler(CallbackQueryHandler(button_callback))

    # Запускаем бота
    print("🤖 Бот запущен и готов к работе в группах...")
    print("📌 Не забудьте:")
    print("  1. Добавить бота в группу")
    print("  2. Сделать бота администратором")
    print("  3. Включить у бота права на отправку сообщений")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
