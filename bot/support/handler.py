from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    ContextTypes,

)

from bot.start.handler import menu

async def technical_support(update: Update, context: ContextTypes) -> None:
    # delete user's choice messaege
    await update.message.delete()
    
    # Path to your local image file
    image_path = './test_photo.png'

    # Create an inline keyboard with one button for contacting support
    keyboard = [
        [InlineKeyboardButton("Contact Support", url="https://t.me/x0nescam")],
        [InlineKeyboardButton("Back to Menu", callback_data='menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Enhanced message with Markdown formatting
    message = (
        "*Technical Support*\n"
        "If you have any questions or need assistance, please feel free to reach out to our support team.\n\n"
        "For common issues, you can also check our FAQ section."
    )

    # Send a photo with the message and inline keyboard
    with open(image_path, 'rb') as photo:
        await update.message.reply_photo(
            photo=photo,
            caption=message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )