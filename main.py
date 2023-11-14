#!/usr/bin/env python
# pylint: disable=unused-argument
# This program is dedicated to the public domain under the CC0 license.

"""
First, a few callback functions are defined. Then, those functions are passed to
the Application and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Example of a bot-user conversation using ConversationHandler.
Send /start to initiate the conversation.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import logging
from typing import Dict

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

import firebase_admin
from firebase_admin import credentials, db

cred = credentials.Certificate('./smsbot-d6115-firebase-adminsdk-d6nmx-9bf1103e67.json')
firebase_admin.initialize_app(cred,{'databaseURL': 'https://smsbot-d6115-default-rtdb.firebaseio.com/'})

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Start, show Greeting and an option to see the terms of use (button)
async def start(update: Update, context: ContextTypes) -> None:
    '''Start the conversation and offer options including terms of use, technical support, and profile access.'''

    username = update.message.from_user.username
    keyboard = [
        ["Receive SMS"],  # First row with one button
        ["My Profile", "Technical Support"] # Second row with two buttons
    ]

    #for test add user to db
    await add_test_user_to_db(update, context)
    
    await update.message.reply_text(
        f"Hi {username}! I'm a bot that can help you to receive an SMS to a REAL USA phone number.\n\n"
        "Choose an option from below.",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=False, resize_keyboard=True),
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
    
async def one_time_message_callback(update: Update, context: ContextTypes) -> None:
    # Logic for one-time message
    query = update.callback_query
    await query.answer()  # This is necessary to acknowledge the callback
    await query.edit_message_text("One-time message functionality coming soon.")
    
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


async def technical_support(update: Update, context: ContextTypes) -> None:
    # Path to your local image file
    image_path = './test_photo.png'

    # Create an inline keyboard with one button for contacting support
    keyboard = [
        [InlineKeyboardButton("Contact Support", url="https://t.me/x0nescam")]
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
        
async def add_test_user_to_db(update: Update, context: ContextTypes) -> None:
    user_id = str(update.effective_user.id)  # Convert user ID to string

    now = datetime.utcnow().isoformat() + 'Z'  # Current time in ISO format with UTC indicator

    # Create test transactions and orders
    test_invoices = {
        "inv1": {
            "amount_in_usd": 100,
            "amount_in_crypto": 0.0001,
            "currency": "BTC",
            "crypto_address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
            "timestamp": now,
            "status": "completed"
        },
        "inv2": {
            
            "amount_in_usd": 50,
            "amount_in_crypto": 0.00005,
            "currency": "USDT_TRC20",
            "crypto_address": "TQpQ8JjJ9u7QXKwpQvH8jvX4Qp2mYsUq8t",
            "timestamp": now,
            "status": "expired"
        }
    }

    test_orders_otp = {
        "order1": {
            "price": 10,
            "phone_number": "+1 123 456 7890",
            "timestamp": now,
            "status": "success"
        },
        "order3": {
            "price": 20,
            "phone_number": "+1 123 456 7892",
            "timestamp": now,
            "refunded": True,
            "status": "expired"
        }
    }
    test_orders_rental = {
        "order2": {
            "price": 10,
            "phone_number": "+1 123 456 7890",
            "timestamp": now,
            "rental_period": 15,
            "status": "success"
        },
        "order4": {
            "price": 20,
            "phone_number": "+1 123 456 7893",
            "timestamp": now,
            "rental_period": 30,
            "refunded": False,
            "status": "success"
        }
    }

    # User data including nested transactions and orders
    test_user = {
        'status': 'active',
        'balance': 0,
        'created_at': now,
        'modified_at': now,
        'deleted_at': None,
        'invoices': test_invoices,
        'otp_orders': test_orders_otp,
        'rental_orders': test_orders_rental
    }

    # Reference to the 'users' node in the database
    users_ref = db.reference('users')

    # Adding the test user with nested transactions and orders
    users_ref.child(user_id).set(test_user)


def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    
    
    
  
    application = Application.builder().token("6949445845:AAG9NOA0stm-nD9g2FgN8mMS3DWW7dmXzu0").build()
    
    application.add_handler(CommandHandler("start", start))
    
    application.add_handler(MessageHandler(filters.Regex("^Receive SMS$"), receive_sms))
    application.add_handler(MessageHandler(filters.Regex("^My Profile$"), my_profile))
    application.add_handler(MessageHandler(filters.Regex("^Technical Support$"), technical_support))

    
    #profile callback
    application.add_handler(CallbackQueryHandler(add_balance_callback, pattern='^add_balance$'))
    
    # sms callbacks
    application.add_handler(CallbackQueryHandler(one_time_message_callback, pattern='^one_time_message$'))
    application.add_handler(CallbackQueryHandler(unlimited_messages_callback, pattern='^unlimited_messages$'))
    application.add_handler(CallbackQueryHandler(my_rented_numbers_callback, pattern='^my_rented_numbers$'))
    
    

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()