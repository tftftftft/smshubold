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
from database.methods import firebase_conn


cancel_button = [
    [InlineKeyboardButton("Cancel", callback_data='cancel_action')]
]

ASK_SERVICE_NAME, CONFIRMATION, ORDER_PHONE_NUMBER_OTP = range(3)

# async def one_time_message_callback(update: Update, context: ContextTypes) -> None:
#     # Logic for one-time message
#     query = update.callback_query
#     await query.answer()  # This is necessary to acknowledge the callback
#     await query.edit_message_text("One-time message functionality coming soon.")
    
    
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
    
    service_name_input = update.message.text
    
    ##get price of service and if available
    response = sms_pool.get_service_price('US', service_name_input)
    
    ##get price from response 
    ##{'price': '0.26', 'high_price': '0.75', 'pool': 1, 'success_rate': '100.00'}
    
    ##if response is not available - ask for service name again
    ##{'price': None, 'high_price': None, 'pool': None, 'success_rate': '100.00'}
    if response['price'] is None:

        await update.message.reply_text(
            f"Service {service_name_input} is not available. Please try again.",
            reply_markup=InlineKeyboardMarkup(cancel_button)
        )
        return CONFIRMATION
    
    # Delete the message containing the service name input
    await update.message.delete()
    
    context.user_data['service_name'] = service_name_input
    service_otp_price = response['price']
    context.user_data['service_otp_price'] = service_otp_price
    
    ##ask for confirmation
    keyboard = [[InlineKeyboardButton("Yes", callback_data='yes_confirmation_otp'), InlineKeyboardButton("No", callback_data='no_confirmation_otp')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"The service {context.user_data['service_name']} costs {service_otp_price}. Do you want to proceed?",
        reply_markup=reply_markup
    )
    
    
    return ORDER_PHONE_NUMBER_OTP
    
    

async def not_enough_balance(update: Update, context: ContextTypes) -> int:
    print('not enough balance')
    
    keyboard = [
        [InlineKeyboardButton("Deposit", callback_data="Deposit")]
    ]
    reply_keyboard = InlineKeyboardMarkup(keyboard)

    # Respond to the callback query if it exists
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(
            "You don't have enough balance to rent this number.",
            reply_markup=reply_keyboard
        )
    # Otherwise, respond to a regular message
    elif update.message:
        await update.message.reply_text(
            "You don't have enough balance to rent this number.",
            reply_markup=reply_keyboard
        )
    else:
        print("Update does not contain a message or callback query.")

    return ConversationHandler.END
    
    
async def order_phone_number_otp(update: Update, context: ContextTypes) -> int:
    query = update.callback_query
    await query.answer()
    
    ###check if enough balance
    if firebase_conn.check_if_enough_balance(update.effective_user.id, context.user_data['service_otp_price']) is False:
        await not_enough_balance(update, context)
        return ConversationHandler.END

    ###order phone number
    response = sms_pool.order_sms('US', context.user_data['service_name'], 0, 1, 0)

    ###check if order was successful
    if response['order_id'] is not None:
        order_id = response['order_id']
    ###if not - ask for service name again
    else:
        await query.message.edit_text("There was an error processing your order.")
        return ConversationHandler.END
    
    ###update balance
    if firebase_conn.decrease_balance(update.effective_user.id, 1) is False:
        await query.message.edit_text("There was an error processing your order.")
        return ConversationHandler.END
    
    expires_in = response.get('expires_in', 0)
    start_time = asyncio.get_event_loop().time()  # Get the current loop time

    # Function to update the message
    async def update_message():
        current_time = asyncio.get_event_loop().time()
        elapsed_time = current_time - start_time
        remaining_time = max(expires_in - elapsed_time, 0)
        await query.message.edit_text(
            f"Your phone number is {response['number']}.\n"
            f"Please use this number to receive your OTP for {response['service']}.\n"
            f"This number will expire in {int(remaining_time)} seconds."
        )
        return remaining_time

    await update_message()

    while True:
        await asyncio.sleep(5)
        
        remaining_time = await update_message()
        if remaining_time <= 0:
            await query.message.edit_text("The OTP has expired.")
            break

        check_response = sms_pool.check_sms(order_id)
        print(check_response)
        if check_response['status'] == 3:
            await query.message.edit_text(f"Your OTP is {check_response['full_sms']}.")
            break


    return ConversationHandler.END


    
    
async def cancel(update: Update, context: ContextTypes) -> int:
    """End the conversation."""
    print('cancel')
    
    query = update.callback_query
    await query.answer()
    
    await query.message.edit_text(
        "Canceled"
    )

    return await ask_for_service_name(update, context)


    
otp_conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(ask_for_service_name, pattern='^one_time_message$')],
    conversation_timeout=30,  # Timeout after 5 minutes of inactivity
    states={
        CONFIRMATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, otp_confirmation)],
        ORDER_PHONE_NUMBER_OTP: [CallbackQueryHandler(order_phone_number_otp, pattern='^yes_confirmation_otp$')]
    },
    fallbacks=[
        CallbackQueryHandler(cancel, pattern='^cancel_action$'),
        CallbackQueryHandler(cancel, pattern='^no_confirmation_otp$')
    ]
)