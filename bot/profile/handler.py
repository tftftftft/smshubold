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

from database.methods import firebase_conn

from services.cryptomus.cryptomus_objects import cryptomus

from bot.start.handler import menu

import asyncio



ASK_CRYPTO, PROCESSING_CRYPTO = range(2)

cancel_button = [
    [InlineKeyboardButton("❌ Cancel", callback_data='Cancel')]
]

async def my_profile(update: Update, context: ContextTypes) -> None:
    # delete user's choice messae
    await update.message.delete()
    
    #delete menu message
    if context.user_data.get('menu_message_id') is not None:
        print(context.user_data['menu_message_id'])
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=context.user_data['menu_message_id'])

    # Fetch the user ID
    user_id = update.effective_user.id

    # Create an inline keyboard with one button for adding balance
    keyboard = [
        [InlineKeyboardButton("💰 Add Balance", callback_data='deposit')],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data='menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send a message with the user's ID and the inline keyboard
    await update.message.reply_text(
        f"🆔 *Your ID:* `{user_id}`\n"
        f"💰Your balance: {firebase_conn.get_user_balance(user_id)}$\n",
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    

async def ask_amount(update: Update, context: ContextTypes) -> int:
    """Start the deposit process and ask user for the amount."""
    
    query = update.callback_query
    await query.answer()
    
    ###keyboard for deposit
    keyboard = [
        [InlineKeyboardButton("💵 10$", callback_data='10'), InlineKeyboardButton("💵 20$", callback_data='20'), InlineKeyboardButton("💵 50$", callback_data='50')],
        [InlineKeyboardButton("💵 100$", callback_data='100'), InlineKeyboardButton("💵 200$", callback_data='200'), InlineKeyboardButton("💵 500$", callback_data='500')],
        [InlineKeyboardButton("❌ Cancel", callback_data='menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Use query.message.reply_text to send a new message
    await query.message.edit_text(
        "Please choose the amount you would like to deposit",
        reply_markup=reply_markup
    )
    return ASK_CRYPTO

# async def ask_crypto(update: Update, context: ContextTypes) -> int:
#     """ask for the cryptocurrency."""

#     # amount = update.message.text
#     # context.user_data['amount'] = amount  # Add validation here if needed
    
#     query = update.callback_query
#     await query.answer()
    
#     amount = query.data
#     context.user_data['amount'] = amount
    
#     print(context.user_data['amount'])

    
#     # Directly ask for cryptocurrency
#     keyboard = [
#         [InlineKeyboardButton("💠 BTC", callback_data='BTC'), InlineKeyboardButton("💠 USDT TRC20", callback_data='USDT_TRC20'), InlineKeyboardButton("💠 LTC", callback_data='LTC')],
#         [InlineKeyboardButton("❌ Cancel", callback_data='menu')]
#     ]
#     reply_markup = InlineKeyboardMarkup(keyboard)
        
#     await query.message.edit_text(
#         "Which cryptocurrency would you like to use for the deposit?",
#         reply_markup=reply_markup
#     )
    
#     return PROCESSING_CRYPTO  # Transition to ASK_CRYPTO state

async def process_crypto(update: Update, context: ContextTypes) -> None:
    """Ask the user which cryptocurrency they want to use for the deposit."""
    
    query = update.callback_query
    await query.answer()
    
    # what amount was chosen
    amount = query.data

    try:
        # cryptomus create invoice
        result = cryptomus.create_invoice(amount, 'USD', update.effective_user.id)
        print(result)
        
        invoice_url = result['result']['url']
        
        #create message with invoice url
        confirm_button = InlineKeyboardButton("✅ I've Paid", callback_data='menu')
        await query.message.edit_text(
            f"Please pay the following invoice 👇\nAfter completing the payment, press 'I've Paid'.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💳 Pay Invoice", url=invoice_url)], [confirm_button]])
        )
                
    except Exception as e:
        print(e)
        await query.message.edit_text(
            "❌ Deposit Error!\n"
            "There was an issue processing your deposit. 🚫\n"
            "Please try again later or contact our support team for assistance."
        )
        return await menu(update, context)




# message saying that the payment is being processed
# delete message in 10 seconds
async def payment_successful(update: Update, context: ContextTypes, deposit: int) -> None:
    
    query = update.callback_query
    await query.answer()
    
    payment_successful_message = await query.message.reply_text(
        f"🎉 Payment Successful!\n",
        f"Your deposit of {deposit} has been successfully processed. 🥳\n",
    )
    
    return await menu(update, context)

# async def cancel(update: Update, context: ContextTypes) -> int:
#     """End the conversation."""
#     print('cancel')
    
#     query = update.callback_query
#     await query.answer()

    
#     await menu(update, context)
    
#     return ConversationHandler.END

# async def unexpected_message(update: Update, context: ContextTypes) -> int:
#     await update.message.reply_text("I didn't understand that. Try again.")
#     return ConversationHandler.END

    
# deposit_conv = ConversationHandler(
#     conversation_timeout=30,  # Timeout after 5 minutes of inactivity
#     entry_points=[
#         CallbackQueryHandler(ask_amount, pattern='^Deposit$'),
#     ],
#     states={
        # ASK_CRYPTO: [CallbackQueryHandler(ask_crypto, pattern='^(10|20|50|100|200|500)$')],
        # PROCESSING_CRYPTO: [CallbackQueryHandler(process_crypto, pattern='^(BTC|USDT_TRC20|LTC)$')],
        # PROCESSING_CRYPTO: [CallbackQueryHandler(process_crypto, pattern='^(10|20|50|100|200|500)$')],
#     },
#     fallbacks=[CallbackQueryHandler(cancel, pattern='^Cancel$'), MessageHandler(filters.ALL, unexpected_message)],
# )

