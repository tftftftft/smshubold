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
from bot.start.handler import menu

otp_service_price = 1
otp_not_listed_price = 1.5


otp_cancel_button = [
    [InlineKeyboardButton("❌ Cancel", callback_data='cancel_action')]
]

otp_service_not_found = [
    [InlineKeyboardButton("🔍 Service is not in the list", callback_data='yes_confirmation_otp')],
    [InlineKeyboardButton("❌ Cancel", callback_data='cancel_action')],
]

# Function to update the message
async def update_message(start_time: float, expires_in: int, query: Update, context: ContextTypes) -> int:
    current_time = asyncio.get_event_loop().time()
    elapsed_time = current_time - start_time
    remaining_time = max(expires_in - elapsed_time, 0)
    await query.message.edit_text(
        f"📞 *Your Phone Number:* +`{context.user_data['number']}`\n"
        f"🔐 Use this number to receive your OTP for *{context.user_data['serive']}*.\n"
        f"⏳ This number will expire in {int(remaining_time)} seconds. Act fast!",
        reply_markup=InlineKeyboardMarkup(otp_cancel_button),
        parse_mode="Markdown"
    )
    return remaining_time


ASK_SERVICE_NAME, CONFIRMATION, ORDER_PHONE_NUMBER_OTP, NOT_LISTED_CONFIRMATION, RESEND_OTP = range(5)
    
    
async def ask_for_service_name(update: Update, context: ContextTypes) -> int:

    print('ask for service name')
    
    
    query = update.callback_query
    await query.answer()
    
    
    ask_servie_message = await query.edit_message_text(
        "✍️ Please enter the service name",
        reply_markup=InlineKeyboardMarkup(otp_cancel_button)
    )
    
    context.user_data['otp_ask_service_name_message_id'] = ask_servie_message.message_id
    
    return CONFIRMATION

async def otp_confirmation(update: Update, context: ContextTypes) -> int:
    
    ### check if service name is valid
    ### check price of service
    
    service_name_input = update.message.text.lower()
    
    all_services = sms_pool.get_service_list()
    print(all_services)
    
    
    context.user_data['service_name'] = None
    #get service ID if service name is in the list
    for service in all_services:
        if service_name_input in service['name'].lower():
            context.user_data['service_id'] = service['ID']
            context.user_data['service_name'] = service['name']
            context.user_data['service_otp_price'] = 1
            break



            
    ##get price of service and if available
    response = sms_pool.get_service_price('US', context.user_data['service_name'])
    
    ##get price from response 
    ##{'price': '0.26', 'high_price': '0.75', 'pool': 1, 'success_rate': '100.00'}
    
    ##if response is not available - ask for service name again
    ##{'price': None, 'high_price': None, 'pool': None, 'success_rate': '100.00'}
    if response['price'] is None:

        await update.message.reply_text(
            f"❌ Service {service_name_input} was not found. If the service is not on a list - please choose 'Service is not on a list'.",
            reply_markup=InlineKeyboardMarkup(otp_service_not_found)
        )
        
        context.user_data['service_name'] = "Not Listed"
        context.user_data['service_otp_price'] = 1.5
        
        return ORDER_PHONE_NUMBER_OTP
    
    # Delete the message containing the service name input
    await update.message.delete()
    
    if context.user_data.get('otp_ask_service_name_message_id') is not None:
        #Delete the message asking for service name
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=context.user_data['otp_ask_service_name_message_id'])
    
    ##ask for confirmation
    keyboard = [
        [InlineKeyboardButton(f"✅ Yes - {otp_service_price}$", callback_data='yes_confirmation_otp'), 
        InlineKeyboardButton("❌ No", callback_data='cancel_action')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    confirmation_message = (
    f"💵 The service *{context.user_data['service_name']}* will cost {otp_service_price}$.\n"
    "🤔 Do you want to proceed with the purchase?"
    )

    context.user_data['ask_confirmation_message_id'] = await update.message.reply_text(
        confirmation_message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    
    
    return ORDER_PHONE_NUMBER_OTP
    
    

async def not_enough_balance(update: Update, context: ContextTypes) -> int:
    print('not enough balance')
    
    await update.callback_query.answer()
    
    #delete current message
    await update.callback_query.message.delete()
    
    keyboard = [
        [InlineKeyboardButton("💰 Deposit", callback_data="Deposit")]
    ]
    reply_keyboard = InlineKeyboardMarkup(keyboard)


    await update.callback_query.message.reply_text(
            "❗ You don't have enough balance to rent this number.",
            reply_markup=reply_keyboard
        )

    return ConversationHandler.END
    
    
async def order_phone_number_otp(update: Update, context: ContextTypes) -> int:
    query = update.callback_query
    await query.answer()
    
    ###check if enough balance
    if firebase_conn.check_if_enough_balance(update.effective_user.id, context.user_data['service_otp_price']) is False:
        return await not_enough_balance(update, context)
    
    ###order phone number
    response = sms_pool.order_sms('US', context.user_data['service_name'], 0, 1, 0)

    ###check if order was successful
    if response['order_id'] is not None:
        # order_id = response['order_id']
        ###save data for later
        context.user_data['order_id'] = response['order_id']
        context.user_data['number'] = response['number']
        context.user_data['serive'] = response['service']
    ###if not - ask for service name again
    else:
        await query.message.edit_text("❗ There was an error processing your order.")
        return await cancel(update, context)

    
    expires_in = response.get('expires_in', 0)
    start_time = asyncio.get_event_loop().time()  # Get the current loop time

    # Function to update the message


    await update_message(start_time=start_time, expires_in=expires_in, query=query, context=context)

    async def accept_message() -> int:
        while True:
            print('while')
        
            await asyncio.sleep(5)
            
            if context.user_data.get('conversation_ended'):
                break
            
            remaining_time = await update_message(start_time=start_time, expires_in=expires_in, query=query, context=context)
            print(remaining_time)
            if remaining_time <= 15:
                await query.message.edit_text(
                    "❗ The phone number has expired.",
                    reply_markup=InlineKeyboardMarkup(otp_cancel_button)
                    )
                break
                

            check_response = sms_pool.check_sms(context.user_data['order_id'])
            print(check_response)
            if check_response['status'] == 3:
                
                ###update balance
                if firebase_conn.decrease_balance(update.effective_user.id, 1) is False:
                    await query.message.edit_text("❗ There was an error processing your order.")
                
                keyboard = [
                    [InlineKeyboardButton("Use number again? 1$", callback_data='resend_otp')],
                    [InlineKeyboardButton("Back to menu", callback_data='menu')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                    
                ###update message
                await query.message.edit_text(
                    f"Your OTP is {check_response['full_sms']}.",
                    reply_markup=reply_markup
                    )                
                return RESEND_OTP
            
    asyncio.create_task(accept_message())
    
    return RESEND_OTP #?

async def resend_otp(update: Update, context: ContextTypes) -> int:
    query = update.callback_query
    await query.answer()
    
    ###check if enough balance
    if firebase_conn.check_if_enough_balance(update.effective_user.id, context.user_data['service_otp_price']) is False:
        await not_enough_balance(update, context)
        return ConversationHandler.END
    
    ###resend sms
    response = sms_pool.resend(context.user_data['order_id'])
    print(response)
    if response['success'] == 1:
    
        expires_in = 500
        start_time = asyncio.get_event_loop().time()  # Get the current loop time        

        await update_message(start_time=start_time, expires_in=expires_in, query=query, context=context)

    async def chreck_for_resend_message():
        while True:
            print('while')
            await asyncio.sleep(5)
            
            if context.user_data.get('conversation_ended'):
                break
            
            remaining_time = await update_message(start_time=start_time, expires_in=expires_in, query=query, context=context)
            if remaining_time <= 15:
                await query.message.edit_text("The phone number has expired.")
                return await cancel(update, context)

            check_response = sms_pool.check_sms(context.user_data['order_id'])
            print(check_response)
            if check_response['status'] == 3:
                
                ###update balance
                firebase_conn.decrease_balance(update.effective_user.id, 1)
                
                ###update message
                await query.message.edit_text(
                    f"Your OTP is {check_response['full_sms']}.",
                    )
                
                print('end - 1')
                
                return await cancel(update, context)
                
                
    
    asyncio.create_task(chreck_for_resend_message())
    
    return ConversationHandler.END
         
    
    
async def cancel(update: Update, context: ContextTypes) -> int:
    """End the conversation."""
    print('cancel')
            
    if update.callback_query is not None:
        print('callback')
        await update.callback_query.answer()
        
        await update.callback_query.message.edit_text(
            "Back to menu"
        )
    else:
        print('message')
        await update.message.edit_text(
            "Back to menu"
        )

    await menu(update, context)
    
    return ConversationHandler.END


    
otp_conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(ask_for_service_name, pattern='^one_time_message$')],
    states={
        CONFIRMATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, otp_confirmation)],
        ORDER_PHONE_NUMBER_OTP: [CallbackQueryHandler(order_phone_number_otp, pattern='^yes_confirmation_otp$')],
        RESEND_OTP: [CallbackQueryHandler(resend_otp, pattern='^resend_otp$')],
    },
    fallbacks=[
        CallbackQueryHandler(cancel, pattern='^cancel_action$'),
        CallbackQueryHandler(cancel, pattern='^no_confirmation_otp$')
    ]
)