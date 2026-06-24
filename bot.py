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

# Словарь для отслеживания статуса пользователей
user_agreements = {}

# Обработчик новых участников
async def new_member_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Проверяем, есть ли новые участники
    for member in update.message.new_chat_members:
        # Пропускаем, если новый участник - сам бот
        if member.id == context.bot.id:
            continue
            
        # Сохраняем в словарь, что пользователь ещё не согласился
        user_agreements[member.id] = False
            
        keyboard = [
            [
                InlineKeyboardButton("✅ Согласен", callback_data=f'agree_{member.id}'),
                InlineKeyboardButton("❌ Отказаться", callback_data=f'decline_{member.id}')
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Отправляем правила новому участнику
        await update.message.reply_text(
            f"👋 Добро пожаловать, {member.first_name}!\n\n{RULES_TEXT}",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

# Функция для кика пользователя
async def kick_user(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int, reason: str = "Отказ от правил"):
    """Универсальная функция для кика пользователя"""
    try:
        # Пытаемся забанить пользователя
        await context.bot.ban_chat_member(
            chat_id=chat_id,
            user_id=user_id
        )
        logging.info(f"✅ Пользователь {user_id} забанен в чате {chat_id}")
        
        # Разбаниваем, чтобы пользователь мог зайти позже (эффект "кика")
        await context.bot.unban_chat_member(
            chat_id=chat_id,
            user_id=user_id
        )
        logging.info(f"✅ Пользователь {user_id} разбанен (кик выполнен)")
        
        return True
    except Exception as e:
        logging.error(f"❌ Ошибка при кике пользователя {user_id}: {e}")
        return False

# Обработчик нажатия на кнопку
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # Получаем ID пользователя и действие из callback_data
    action, user_id = query.data.split('_')
    user_id = int(user_id)
    chat_id = update.effective_chat.id
    
    # Проверяем, что кнопку нажимает тот же пользователь
    if query.from_user.id != user_id:
        await query.answer("❌ Эта кнопка не для вас!", show_alert=True)
        return
    
    # Обработка согласия
    if action == 'agree':
        user_agreements[user_id] = True
        await query.edit_message_text(
            f"✅ *Спасибо, {query.from_user.first_name}! Вы приняли правила.*\n\n"
            f"Теперь вы можете общаться в чате.\n"
            f"Добро пожаловать! 🎉",
            parse_mode='Markdown'
        )
        
        # Отправляем приветствие в чат
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"👋 Приветствуем нового участника: {query.from_user.mention_html()}!\n"
                 f"Он принял правила и готов к общению!",
            parse_mode='HTML'
        )
    
    # Обработка отказа - КИКАЕМ ПОЛЬЗОВАТЕЛЯ!
    elif action == 'decline':
        user_agreements[user_id] = False
        
        # Сначала показываем сообщение об отказе
        await query.edit_message_text(
            f"❌ *{query.from_user.first_name}, вы отказались от принятия правил.*\n\n"
            f"К сожалению, без принятия правил вы не можете участвовать в чате.\n"
            f"Вы будете удалены из чата.",
            parse_mode='Markdown'
        )
        
        # Пытаемся кикнуть пользователя
        kick_success = await kick_user(
            context=context,
            chat_id=chat_id,
            user_id=user_id,
            reason="Отказ от правил"
        )
        
        if kick_success:
            # Отправляем уведомление в чат
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"🔨 Пользователь {query.from_user.mention_html()} был удалён из чата за отказ от правил.",
                parse_mode='HTML'
            )
            
            # Отправляем пользователю сообщение о кике (в ЛС)
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"❌ Вы были удалены из чата за отказ от правил.\n"
                         f"Если передумаете, вы сможете заново вступить в чат и принять правила."
                )
            except:
                pass  # Если не можем написать в ЛС
        else:
            # Если кик не удался - предупреждаем админов
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"⚠️ <b>ВНИМАНИЕ!</b>\n"
                     f"Не удалось удалить пользователя {query.from_user.mention_html()}!\n"
                     f"Проверьте права бота: нужны права на <b>блокировку пользователей</b>.",
                parse_mode='HTML'
            )

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Получаем username бота
    bot_username = context.bot.username
    
    keyboard = [
        [InlineKeyboardButton("➕ Добавить в группу", url=f"https://t.me/{bot_username}?startgroup=start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🤖 *Привет! Я бот для управления правилами группы.*\n\n"
        "📌 *Мои функции:*\n"
        "• Приветствую новых участников\n"
        "• Показываю правила чата\n"
        "• Запрашиваю согласие с правилами\n"
        "• 🔨 Удаляю тех, кто отказался\n\n"
        "🔧 *Как использовать:*\n"
        "1. Добавьте меня в группу\n"
        "2. Сделайте меня администратором с правами:\n"
        "   ✅ Отправка сообщений\n"
        "   ✅ Удаление сообщений\n"
        "   ✅ Блокировка пользователей\n"
        "3. Готово! Я буду автоматически работать\n\n"
        "👑 *Команды для админов:*\n"
        "/rules - показать правила\n"
        "/stats - статистика согласий",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

# Команда для показа правил
async def show_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Проверяем, что команду вызвал админ
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        if member.status not in ['creator', 'administrator']:
            await update.message.reply_text("❌ Эта команда только для администраторов!")
            return
    except:
        await update.message.reply_text("❌ Ошибка проверки прав!")
        return
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Согласен", callback_data=f'agree_{user_id}'),
            InlineKeyboardButton("❌ Отказаться", callback_data=f'decline_{user_id}')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"📜 *Правила чата*\n\n{RULES_TEXT}",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

# Команда для просмотра статистики
async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Проверяем, что команду вызвал админ
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        if member.status not in ['creator', 'administrator']:
            await update.message.reply_text("❌ Эта команда только для администраторов!")
            return
    except:
        await update.message.reply_text("❌ Ошибка проверки прав!")
        return
    
    # Считаем статистику
    total = len(user_agreements)
    agreed = sum(1 for v in user_agreements.values() if v)
    declined = total - agreed
    
    stats_text = (
        f"📊 *Статистика принятия правил*\n\n"
        f"👥 Всего участников: {total}\n"
        f"✅ Согласились: {agreed}\n"
        f"❌ Отказались и кикнуты: {declined}"
    )
    
    await update.message.reply_text(stats_text, parse_mode='Markdown')

# Основная функция
def main():
    # Создаём приложение
    application = Application.builder().token(BOT_TOKEN).build()

    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("rules", show_rules))
    application.add_handler(CommandHandler("stats", show_stats))
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_member_handler))
    application.add_handler(CallbackQueryHandler(button_callback))

    print("🤖 Бот запущен и готов к работе в группах...")
    print("📌 Не забудьте:")
    print("  1. Добавить бота в группу")
    print("  2. Сделать бота администратором")
    print("  3. Включить права на:")
    print("     ✅ Отправка сообщений")
    print("     ✅ Удаление сообщений")
    print("     ✅ Блокировка пользователей (ЭТО ВАЖНО ДЛЯ КИКА!)")
    print("  4. Заменить BOT_TOKEN на ваш токен")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
