

import logging
from typing import Dict
import os
from dotenv import load_dotenv
load_dotenv()  # This loads the variables from .env


from bot.support.handler import technical_support
from bot.sms.handler import receive_sms, one_time_message_callback, unlimited_messages_callback, my_rented_numbers_callback
from bot.profile.handler import my_profile, add_balance_callback
from bot.start.handler import start

from database.methods import FirebaseService

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
logging.getLogger.setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


    
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

db = FirebaseService(database_url=f'{os.getenv("FIREBASE_URL")}', credential_path=f'{os.getenv("FIREBASE_ACCESS_JSON_PATH")}')

def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.

    logger.info("Starting bot")

    application = Application.builder().token(os.getenv("BOT_TOKEN")).build()
    
    
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