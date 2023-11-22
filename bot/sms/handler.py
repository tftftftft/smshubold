from datetime import datetime
import asyncio
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    PicklePersistence,
    filters,
    CallbackQueryHandler,

)

from services.smspool_objects import sms_pool


async def receive_sms(update: Update, context: ContextTypes) -> None:
    # Logic for receiving SMS
    keyboard = [
        [InlineKeyboardButton("One-time message", callback_data='one_time_message')],
        [InlineKeyboardButton("Rent Phone Number", callback_data='rent_number')],
        [InlineKeyboardButton("My Rented Numbers", callback_data='my_rented_numbers')]
    ]
    
    await update.message.reply_text(
        "Choose an option from below.",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    
    
    
#####rental

# 1. Message saying that only 30 days rental is available | any service
# 2. Activate and show the number

cancel_button = [
    [InlineKeyboardButton("Cancel", callback_data='cancel_action')]
]

rental_faq_button = [
    [InlineKeyboardButton("Buy", callback_data='buy_rental')],
    [InlineKeyboardButton("Cancel", callback_data='cancel_action')]
]

RENTAL_FAQ, RENTAL_CONFIRMATION, RENTAL_FINAL = range(3)

async def rental_faq(update: Update, context: ContextTypes) -> int:
    
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "Only 30 days rental is available for any service.",
        reply_markup=InlineKeyboardMarkup(rental_faq_button)
    )
    
    return RENTAL_FINAL

async def rental_final(update: Update, context: ContextTypes) -> int:
    
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "Your number will be activated within 24 hours.",
        reply_markup=InlineKeyboardMarkup(cancel_button)
    )
    
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes) -> int:
    """End the conversation."""
    print('cancel')
    
    query = update.callback_query
    await query.answer()
    
    await query.message.edit_text(
        "Canceled"
    )

    return await rental_faq(update, context)


    
rental_conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(rental_faq, pattern='^rent_number$')],
    conversation_timeout=30,  # Timeout after 5 minutes of inactivity
    states={
        RENTAL_FINAL: [CallbackQueryHandler(rental_final, pattern='^buy_rental$')]
    },
    fallbacks=[
        CallbackQueryHandler(cancel, pattern='^cancel_action$')
    ]
)
    
async def unlimited_messages_callback(update: Update, context: ContextTypes) -> None:
    # Logic for unlimited messages
    query = update.callback_query
    await query.answer()  # This is necessary to acknowledge the callback
    await query.edit_message_text("Unlimited messages functionality coming soon.")
    
async def my_rented_numbers_callback(update: Update, context: ContextTypes) -> None:
    # Logic for my rented numbers
    query = update.callback_query
    await query.answer()  # This is necessary to acknowledge the callback
    await query.edit_message_text("My rented numbers functionality coming soon.")