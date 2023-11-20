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

    print('start_deposit')
    
    query = update.callback_query
    await query.answer()
    
    # Use query.message.reply_text to send a new message
    await query.edit_message_text(
        "Please enter the amount you would like to deposit in $:",
        reply_markup=InlineKeyboardMarkup(cancel_button)
    )
    return ASK_CRYPTO

async def ask_crypto(update: Update, context: ContextTypes) -> int:
    """ask for the cryptocurrency."""

    amount = update.message.text
    context.user_data['amount'] = amount  # Add validation here if needed
    # Directly ask for cryptocurrency
    keyboard = [
        [InlineKeyboardButton("BTC", callback_data='BTC'), InlineKeyboardButton("USDT TRC20", callback_data='USDT_TRC20'), InlineKeyboardButton("LTC", callback_data='LTC')],
        [InlineKeyboardButton("Cancel", callback_data='Cancel')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
        
    await update.message.reply_text(
        "Which cryptocurrency would you like to use for the deposit?",
        reply_markup=reply_markup
    )
    
    return PROCESSING_CRYPTO  # Transition to ASK_CRYPTO state

async def process_crypto(update: Update, context: ContextTypes) -> int:
    """Ask the user which cryptocurrency they want to use for the deposit."""
    print('ask_crypto')
    
    query = update.callback_query
    await query.answer()
    
    #what crypto chosen
    crypto = query.data
    print(crypto, "chosen")
    
    #get usd amount based on crypto
    #generate crypto address

    crypto_address = "address"
    

       
    await query.message.edit_text(
        f"Please send {context.user_data['amount']} {crypto} to the following address: {crypto_address}",
        reply_markup=InlineKeyboardMarkup(cancel_button)
    )
    
    await asyncio.sleep(5)
    #wait for callback from gateway
    #imitate for now
    await query.message.edit_text(
        "Please wait for the transaction to be confirmed."
    )
    
    await asyncio.sleep(5)
    
    await query.message.edit_text(
        "Your deposit has been confirmed."        
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
        ASK_CRYPTO: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_crypto)],
        PROCESSING_CRYPTO: [CallbackQueryHandler(process_crypto, pattern='^(BTC|USDT_TRC20|LTC)$')],
    },
    fallbacks=[CallbackQueryHandler(cancel, pattern='^Cancel$'), MessageHandler(filters.ALL, unexpected_message)],
)

