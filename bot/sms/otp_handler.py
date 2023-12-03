from datetime import datetime
import asyncio
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
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
from bot.start.handler import menu, light_menu
from utilities.utils import user_data_store

otp_service_price = 1
otp_service_high_price = 2
otp_not_listed_price = 1.5





otp_cancel_button = [
    [InlineKeyboardButton("❌ Cancel", callback_data='menu')]
]


back_to_menu_button = [
    [InlineKeyboardButton("🔙 Back to Menu", callback_data='menu')]
]

otp_service_not_found = [
    [InlineKeyboardButton("🔍 Service is not in the list - 2$", callback_data='yes_confirmation_otp')],
    [InlineKeyboardButton("❌ Cancel", callback_data='menu')],
]

async def refund_number(update: Update, context: ContextTypes) -> int:
    #refund number
    #menu
    
    query = update.callback_query
    await query.answer()
    
    # get order id from query
    order_id = query.data.split('_')[-1]
    
    response = sms_pool.cancel_sms(order_id)
    print(response)
    
    #return to menu
    await menu(update, context)
    
async def count_price(price_from_request: str) -> float:
    if float(price_from_request) > 0.7:
        return otp_service_high_price
    else:
        return otp_service_price


# Function to update the message
async def update_message(start_time: float, expires_in: int, phone_number: str, service_name: str, order_id: str, query: Update, context: ContextTypes) -> int:
    current_time = asyncio.get_event_loop().time()
    elapsed_time = current_time - start_time
    remaining_time = max(expires_in - elapsed_time, 0)
    
    otp_cancel_refund_button = [
    [InlineKeyboardButton("❌ Cancel", callback_data=f'otp_cancel_refund_{order_id}')],
    ]
    
    await query.message.edit_text(
        f"📞 *Your Phone Number:* +`{phone_number}`\n"
        f"🔐 Use this number to receive your OTP for *{service_name}*.\n"
        f"⏳ This number will expire in {int(remaining_time/60)} minutes. Act fast!",
        reply_markup=InlineKeyboardMarkup(otp_cancel_refund_button),
        parse_mode="Markdown"
    )
    return remaining_time



async def accept_message(user_id: int,order_id: str, service_otp_price: float, start_time: float, expires_in: float, phone_number: str, service_name:str, query: CallbackQuery, context: ContextTypes) -> int:
    while True:
        print('while')
    
        await asyncio.sleep(60)
        
        if context.user_data.get('conversation_ended'):
            break
        
        remaining_time = await update_message(start_time=start_time, expires_in=expires_in, phone_number=phone_number, service_name=service_name, order_id=order_id, query=query, context=context)
        print(remaining_time)
        if remaining_time <= 15:
            await query.message.edit_text(
                "❗ The phone number has expired.",
                reply_markup=InlineKeyboardMarkup(otp_cancel_button)
                )
            break
            

        check_response = await sms_pool.check_sms(order_id)
        print(check_response)
        if check_response['status'] == 3:
            
            ###update balance
            if firebase_conn.decrease_balance(user_id, service_otp_price) is False:
                await query.message.edit_text("❗ There was an error processing your order.")
            
            keyboard = [
                [InlineKeyboardButton("Use number again? - 1$", callback_data='resend_otp')],
                [InlineKeyboardButton("Back to menu", callback_data='menu')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
                
            ###update message
            await query.message.edit_text(
                f"Your message is *{check_response['full_sms']}*.",
                reply_markup=reply_markup,
                parse_mode="Markdown"
                )                
            break
        
        
async def check_for_resend_message(user_id: int, order_id: str, start_time: float, expires_in: float, phone_number: str, service_name:str, query: CallbackQuery, update: Update, context: ContextTypes):
    while True:
        print('while')
        await asyncio.sleep(60)
        
        if context.user_data.get('conversation_ended'):
            break
        
        remaining_time = await update_message(start_time=start_time, expires_in=expires_in, phone_number=phone_number, service_name=service_name, order_id=order_id, query=query, context=context)
        if remaining_time <= 15:
            await query.message.edit_text("The phone number has expired.")
            return await menu(update, context)

        check_response = await sms_pool.check_sms(order_id)
        print(check_response)
        if check_response['status'] == 3:
            
            ###update balance
            firebase_conn.decrease_balance(user_id, 1) ###FIXED 1$ for resend 
            
            ###update message
            await query.message.edit_text(
                f"Your message is *{check_response['full_sms']}*.",
                reply_markup=InlineKeyboardMarkup(back_to_menu_button),
                parse_mode="Markdown"
                )
            
            break
        
async def get_all_services_chat(update: Update) -> dict:
    #loading message
    loading_message = await update.message.reply_text(
        "⏳ Please wait while we are processing your request."
    )
    
    try:
        all_services = await sms_pool.get_service_list()
        print(all_services)
        #delete loading message
        await loading_message.delete()
        return all_services

    except Exception as e:
        print(e)
        await update.message.edit_text(
            "❗ There was an error processing your order.",
            reply_markup=InlineKeyboardMarkup(otp_cancel_button)
        )
        return None


async def lookup_service(all_services: dict, searching_service_name: str) -> (str, str):
    print(all_services)
    for service in all_services:
        if searching_service_name.lower() in service['name'].lower():
            return service['ID'], service['name']
    return None, None

async def otp_order_number(update: Update, query: CallbackQuery, context: ContextTypes) -> dict:
    
    ###show loading message
    loading_message = await query.message.reply_text(
        "⏳ Please wait while we are processing your request."
    )
    
    ###order phone number
    try:
        response = await sms_pool.order_sms('US', context.user_data['otp_service_name'], 0, 1, 0)
        
        await loading_message.delete()
        
        return response
    except Exception as e:
        print(e)
        await query.message.edit_text(
            "❗ There was an error processing your order.",
            reply_markup=InlineKeyboardMarkup(otp_cancel_button))
        
        await loading_message.delete()
        
        await menu(update, context)
        
        return None
    



##########################
ASK_SERVICE_NAME, CONFIRMATION, ORDER_PHONE_NUMBER_OTP, NOT_LISTED_CONFIRMATION, RESEND_OTP = range(5)
    
    
async def ask_for_service_name(update: Update, context: ContextTypes) -> int:

    print('ask for service name')
    
    
    query = update.callback_query
    await query.answer()
    
    ###for future cancel  
    context.user_data['conversation_ended'] = False
    
    ###ask for service name
    ask_service_message = await query.edit_message_text(
        "✍️ Please enter the service name",
        reply_markup=InlineKeyboardMarkup(otp_cancel_button)
    )
    
    user_id = update.effective_user.id
    value = user_data_store[user_id] = {'otp_ask_service_name_message_id': ask_service_message.message_id}
    print(value, 'ask service message id')
    ###save message id for future deletion
    # context.user_data['otp_ask_service_name_message_id'] = ask_service_message.message_id
    # print(context.user_data['otp_ask_service_name_message_id'], 'ask service message id')

  
    
    return CONFIRMATION

async def otp_confirmation(update: Update, context: ContextTypes) -> int:
    
    ### check if service name is valid
    ### check price of service
    
    service_name_input = update.message.text.lower()
    
    all_services = await get_all_services_chat(update)

    # Delete the message containing the service name input
    await update.message.delete()
    
    # Delete the message asking for service name
    user_id = update.effective_user.id
    message_id = user_data_store.get(user_id, {}).get('otp_ask_service_name_message_id')
    print(message_id, 'message id')
    print(user_data_store, 'user data store')
    if message_id:
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=message_id)
        


    context.user_data['otp_service_name'] = None
    #get service ID if service name is in the list
    service_id, service_name = await lookup_service(all_services, service_name_input)
    
    ##get price of service
    
    if service_id is not None:
        print(service_id, service_name)
        context.user_data['otp_service_id'] = service_id 
        context.user_data['otp_service_name'] = service_name
            
        response = await sms_pool.get_service_price('US', context.user_data['otp_service_name'])    
    
        ##get price from response 
        ##{'price': '0.26', 'high_price': '0.75', 'pool': 1, 'success_rate': '100.00'}
        
        ##if response is not available - ask for service name again
        ##{'price': None, 'high_price': None, 'pool': None, 'success_rate': '100.00'}

        context.user_data['otp_service_price'] = await count_price(response['price'])
        print(context.user_data['otp_service_price'])
        
        ##ask for confirmation
        otp_confirmation_keyboard = [
            [InlineKeyboardButton(f"✅ Yes - {context.user_data['otp_service_price']}$", callback_data='yes_confirmation_otp'), 
            InlineKeyboardButton("❌ No", callback_data='menu')]
        ]
        reply_markup = InlineKeyboardMarkup(otp_confirmation_keyboard)
        
        confirmation_message = (
        f"💵 The service *{context.user_data['otp_service_name']}* will cost {context.user_data['otp_service_price']}$.\n"
        "🤔 Do you want to proceed with the purchase?"
        )

        context.user_data['otp_ask_confirmation_message_id'] = await update.message.reply_text(
            confirmation_message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        
    else:
        await update.message.reply_text(
            f"❌ Service {service_name_input} was not found. If the service is not on a list - please choose 'Service is not on a list'.",
            reply_markup=InlineKeyboardMarkup(otp_service_not_found)
        )
        
        context.user_data['otp_service_name'] = "Not Listed"
        context.user_data['otp_service_price'] = otp_not_listed_price
        

    return ConversationHandler.END    
    

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
    
    print(context.user_data['otp_service_price'])
    ###check if enough balance
    if firebase_conn.check_if_enough_balance(update.effective_user.id, context.user_data['otp_service_price']) is False:
        return await not_enough_balance(update, context)
    
    response = await otp_order_number(update, query, context)

    ###check if order was successful
    if response['order_id'] is not None:
        # order_id = response['order_id']
        ###save data for later
        context.user_data['otp_order_id'] = response['order_id']
        context.user_data['otp_number'] = response['number']
        context.user_data['otp_service'] = response['service']
        
        
        ### start accepting messages
        expires_in = 1000
        start_time = asyncio.get_event_loop().time()  # Get the current loop time

        ### update message
        await update_message(start_time=start_time, expires_in=expires_in, phone_number=context.user_data['otp_number'], service_name=context.user_data['otp_service'], order_id=response['order_id'], query=query, context=context)

        context.user_data['conversation_ended'] = False
                
        asyncio.create_task(accept_message(update.effective_user.id,context.user_data['otp_order_id'], context.user_data['otp_service_price'],
                                        start_time, expires_in, context.user_data['otp_number'], context.user_data['otp_service'], query, context))
        
    ###if not - ask for service name again
    else:
        await query.message.edit_text("❗ There was an error processing your order.")
        await menu(update, context)

async def resend_otp(update: Update, context: ContextTypes) -> int:
    query = update.callback_query
    await query.answer()
    
    ###check if enough balance
    if firebase_conn.check_if_enough_balance(update.effective_user.id, context.user_data['otp_service_price']) is False:
        await not_enough_balance(update, context)
        return ConversationHandler.END
    
    ###resend sms
    response = await sms_pool.resend(context.user_data['otp_order_id'])
    print(response)
    if response['success'] == 1:
    
        expires_in = 500
        start_time = asyncio.get_event_loop().time()  # Get the current loop time        

        await update_message(start_time=start_time, expires_in=expires_in, phone_number=context.user_data['otp_number'], service_name=context.user_data['otp_service'], order_id=context.user_data['otp_order_id'], query=query, context=context)

        ### set conversation_ended to False for cancel
        context.user_data['conversation_ended'] = False
        
        asyncio.create_task(check_for_resend_message(user_id=update.effective_user.id, order_id=context.user_data['otp_order_id'], start_time=start_time, 
                                                      expires_in=expires_in, phone_number=context.user_data['otp_number'], service_name=context.user_data['otp_service'], query=query, update=update, context=context))
    else:
        await query.message.edit_text("❗ The number doesn't support resend.")
        return await menu(update, context)
         
    
    
async def cancel(update: Update, context: ContextTypes) -> int:
    """End the conversation."""
    print('cancel')
    
    context.user_data['conversation_ended'] = True
            
    # if update.callback_query is not None:
    #     print('callback')
    #     await update.callback_query.answer()
        
    #     await update.callback_query.message.edit_text(
    #         "Back to menu"
    #     )
    # else:
    #     print('message')
    #     await update.message.edit_text(
    #         "Back to menu"
    #     )

    await light_menu(update, context)
    
    return ConversationHandler.END


    
# otp_conv = ConversationHandler(
#     entry_points=[CallbackQueryHandler(ask_for_service_name, pattern='^one_time_message$')],
#     states={
#         CONFIRMATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, otp_confirmation)],
#         ORDER_PHONE_NUMBER_OTP: [CallbackQueryHandler(order_phone_number_otp, pattern='^yes_confirmation_otp$')],
#         RESEND_OTP: [CallbackQueryHandler(resend_otp, pattern='^resend_otp$')],
#     },
#     fallbacks=[
#         CallbackQueryHandler(cancel, pattern='^cancel_action$'),
#         CallbackQueryHandler(cancel, pattern='^no_confirmation_otp$')
#     ]
# )

otp_conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(ask_for_service_name, pattern='^one_time_message$')],
    states={
        CONFIRMATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, otp_confirmation)],
        # ORDER_PHONE_NUMBER_OTP: [CallbackQueryHandler(order_phone_number_otp, pattern='^yes_confirmation_otp$')],
        # RESEND_OTP: [CallbackQueryHandler(resend_otp, pattern='^resend_otp$')],
    },
    fallbacks=[
        CallbackQueryHandler(cancel, pattern='^cancel_action$'),
        CallbackQueryHandler(cancel, pattern='^no_confirmation_otp$')
    ]
)

