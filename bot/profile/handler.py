from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    ContextTypes,
)




async def my_profile(update: Update, context: ContextTypes) -> None:
    # Fetch the user ID
    user_id = update.effective_user.id

    # Create an inline keyboard with one button for adding balance
    keyboard = [
        [InlineKeyboardButton("Add Balance", callback_data='add_balance')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send a message with the user's ID and the inline keyboard
    await update.message.reply_text(
        f"Your ID is: {user_id}\n\nClick below to add balance:",
        reply_markup=reply_markup
    )
    
    
async def add_balance_callback(update: Update, context: ContextTypes) -> None:
    # Logic for adding balance
    query = update.callback_query
    await query.answer()  # This is necessary to acknowledge the callback
    await query.edit_message_text("Add balance functionality coming soon.")
