from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove, Bot
from telegram.constants import ParseMode
from telegram.ext import (
    ContextTypes,
    Application,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
)

from models.models import User

from  database.methods import firebase_conn

import asyncio



ASK_CRYPTO, PROCESSING_CRYPTO = range(2)

cancel_button = [
    [InlineKeyboardButton("Cancel", callback_data='Cancel')]
]

async def my_profile(update: Update, context: ContextTypes) -> None:
    # Fetch the user ID
    user_id = update.effective_user.id

    # Create an inline keyboard with one button for adding balance
    keyboard = [
        [InlineKeyboardButton("Add Balance", callback_data='Deposit')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send a message with the user's ID and the inline keyboard
    await update.message.reply_text(
        f"Your ID is: {user_id}\n\nClick below to add balance:",
        reply_markup=reply_markup
    )
    

async def ask_amount(update: Update, context: ContextTypes) -> int:
    """Start the deposit process and ask user for the amount."""
    
    query = update.callback_query
    await query.answer()
    
    ###keyboard for deposit
    keyboard = [
        [InlineKeyboardButton("10$", callback_data='10'), InlineKeyboardButton("20$", callback_data='20'), InlineKeyboardButton("50$", callback_data='50')],
        [InlineKeyboardButton("100$", callback_data='100'), InlineKeyboardButton("200$", callback_data='200'), InlineKeyboardButton("500$", callback_data='500')],
        [InlineKeyboardButton("Cancel", callback_data='Cancel')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Use query.message.reply_text to send a new message
    await query.message.edit_text(
        "Please choose the amount you would like to deposit",
        reply_markup=reply_markup
    )
    return ASK_CRYPTO

async def ask_crypto(update: Update, context: ContextTypes) -> int:
    """ask for the cryptocurrency."""

    # amount = update.message.text
    # context.user_data['amount'] = amount  # Add validation here if needed
    
    query = update.callback_query
    await query.answer()
    
    amount = query.data
    context.user_data['amount'] = amount
    
    print(context.user_data['amount'])

    
    # Directly ask for cryptocurrency
    keyboard = [
        [InlineKeyboardButton("BTC", callback_data='BTC'), InlineKeyboardButton("USDT TRC20", callback_data='USDT_TRC20'), InlineKeyboardButton("LTC", callback_data='LTC')],
        [InlineKeyboardButton("Cancel", callback_data='Cancel')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
        
    await query.message.edit_text(
        "Which cryptocurrency would you like to use for the deposit?",
        reply_markup=reply_markup
    )
    
    return PROCESSING_CRYPTO  # Transition to ASK_CRYPTO state

async def process_crypto(update: Update, context: ContextTypes) -> int:
    """Ask the user which cryptocurrency they want to use for the deposit."""
    
    query = update.callback_query
    await query.answer()
    
    #what crypto chosen
    crypto = query.data
    
    #get usd amount based on crypto
    #generate crypto address

    crypto_address = "address"
    
    
    ###generate invoice
       
    await query.message.edit_text(
        f"Please send {context.user_data['amount']} {crypto} to the following address: {crypto_address}",
        reply_markup=InlineKeyboardMarkup(cancel_button)
    )
    
    ###wait for callback from gateway
    asyncio.sleep(5)
    
    ###when callback received - add balance to user and update balance in db
    #get user id
    user_id = str(update.effective_user.id)
    result = firebase_conn.add_balance(user_id, context.user_data['amount'])

    if result:
        await query.message.edit_text(
            "Your deposit has been confirmed."        
        )
    else:
        await query.message.edit_text(
            "There was an error processing your deposit. Please try again later or contact support."        
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

async def unexpected_message(update: Update, context: ContextTypes) -> int:
    await update.message.reply_text("I didn't understand that. Try again.")
    return ConversationHandler.END

    
deposit_conv = ConversationHandler(
    conversation_timeout=30,  # Timeout after 5 minutes of inactivity
    entry_points=[
        CallbackQueryHandler(ask_amount, pattern='^Deposit$'),
    ],
    states={
        ASK_CRYPTO: [CallbackQueryHandler(ask_crypto, pattern='^(10|20|50|100|200|500)$')],
        PROCESSING_CRYPTO: [CallbackQueryHandler(process_crypto, pattern='^(BTC|USDT_TRC20|LTC)$')],
    },
    fallbacks=[CallbackQueryHandler(cancel, pattern='^Cancel$'), MessageHandler(filters.ALL, unexpected_message)],
)

