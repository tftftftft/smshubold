from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    ContextTypes,

)

from bot.start.handler import menu

async def technical_support(update: Update, context: ContextTypes) -> None:
    # delete user's choice messaege
    await update.message.delete()
    
    #delete menu message
    if context.user_data.get('menu_message_id') is not None:
        print(context.user_data['menu_message_id'])
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=context.user_data['menu_message_id'])
    
    # Path to your local image file
    image_path = './files/test_photo.png'

    # Create an inline keyboard with one button for contacting support
    keyboard = [
        [InlineKeyboardButton("🆘 Contact Support", url="https://t.me/x0nescam")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data='menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Enhanced message with Markdown formatting
    message = (
        "*🛠 Technical Support*\n\n"
        "Got questions or need help? Don't hesitate to reach out to our support team! 🤝\n\n"
        "You can also visit our FAQ section for quick answers to common queries. Just click the buttons below for more information or to get in touch with us directly. 👇"
    )

    # Send a photo with the message and inline keyboard
    with open(image_path, 'rb') as photo:
        await update.message.reply_photo(
            photo=photo,
            caption=message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )