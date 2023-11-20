from datetime import datetime
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


async def receive_sms(update: Update, context: ContextTypes) -> None:
    # Logic for receiving SMS
    keyboard = [
        [InlineKeyboardButton("One-time message", callback_data='one_time_message')],
        [InlineKeyboardButton("Rent Phone Number", callback_data='unlimited_messages')],
        [InlineKeyboardButton("My Rented Numbers", callback_data='my_rented_numbers')]
    ]
    
    await update.message.reply_text(
        "Choose an option from below.",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    
    
    

#####################

cancel_button = [
    [InlineKeyboardButton("Cancel", callback_data='Cancel')]
]

ASK_SERVICE_NAME, CONFIRMATION, ORDER_PHONE_NUMBER_OTP = range(3)

async def one_time_message_callback(update: Update, context: ContextTypes) -> None:
    # Logic for one-time message
    query = update.callback_query
    await query.answer()  # This is necessary to acknowledge the callback
    await query.edit_message_text("One-time message functionality coming soon.")
    
    
    
    
async def ask_for_service_name(update: Update, context: ContextTypes) -> int:
    
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "Please enter service name (Gmail) or 0 if can't find the service:",
        reply_markup=InlineKeyboardMarkup(cancel_button)
    )
    
    
    
    return CONFIRMATION

async def otp_confirmation(update: Update, context: ContextTypes) -> int:
    
    ### check if service name is valid
    ### check price of service
    
    service_name = update.message.text
    context.user_data['service_name'] = service_name
    
    
    keyboard = [[InlineKeyboardButton("Yes", callback_data='yes_confirmation_otp'), InlineKeyboardButton("No", callback_data='no_confirmation_otp')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"The service {context.user_data['service_name']} costs $1. Do you want to proceed?",
        reply_markup=reply_markup
    )
    
    return ORDER_PHONE_NUMBER_OTP
    
    
async def order_phone_number_otp(update: Update, context: ContextTypes) -> int:
    ##placeholder
    
    query = update.callback_query
    await query.answer()
    
    await query.message.edit_text(
        "Please wait while we order a phone number for you."    
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
    return ConversationHandler.END


    
otp_conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(ask_for_service_name, pattern='^one_time_message$')],
    states={
        CONFIRMATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, otp_confirmation)],
        ORDER_PHONE_NUMBER_OTP: [CallbackQueryHandler(order_phone_number_otp, pattern='^yes_confirmation_otp$')]
    },
    fallbacks=[
        MessageHandler(filters.Regex("^Cancel$"), cancel),
        CallbackQueryHandler(cancel, pattern='^no_confirmation_otp$')
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