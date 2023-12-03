from datetime import datetime
import asyncio
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    JobQueue,
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    PicklePersistence,
    filters,
    CallbackQueryHandler,

)


from bot.start.handler import menu
from bot.sms.rent_history import my_rented_numbers_callback
from utilities.utils import user_data_store


from services.smspool_objects import sms_pool
from database.methods import firebase_conn

service_found_price = 15
service_not_found_price = 20
all_services_price = 30


##817 service id for not listed

cancel_button = [
    [InlineKeyboardButton("❌ Cancel", callback_data='menu')]
]

rental_faq_buttons = [
    [InlineKeyboardButton("✅ Continue", callback_data='continue_rental_1')],
    [InlineKeyboardButton("❌ Cancel", callback_data='menu')]
]

rental_choose_service_buttons = [
    [InlineKeyboardButton("🌐 Any service - 30$", callback_data='any_service_rental')],
    [InlineKeyboardButton("🔍 Specific service - 15$", callback_data='specific_service_rental')],
    [InlineKeyboardButton("❌ Cancel", callback_data='menu')]
]

rental_service_not_found_buttons = [
    [InlineKeyboardButton("🔄 Try again", callback_data='specific_service_rental')],
    [InlineKeyboardButton("❌ Cancel", callback_data='menu')] 
]

rental_confirm_order_buttons = [
    [InlineKeyboardButton("✔️ Confirm", callback_data='confirm_order_specific_service')],
    [InlineKeyboardButton("❌ Cancel", callback_data='menu')]
]

rental_any_service_order_confirmation_buttons = [
    [InlineKeyboardButton("✔️ Confirm", callback_data='confirm_order_any_service')],
    [InlineKeyboardButton("❌ Cancel", callback_data='menu')]
]

# rental_final_buttons = [
#     [InlineKeyboardButton("Go to rentals", callback_data='my_rented_numbers')],
#     [InlineKeyboardButton("Back to Menu", callback_data='menu')]
# ]

async def receive_sms(update: Update, context: ContextTypes) -> None:
    # delete previous message (user's choice)
    await update.message.delete()
    
    #delete menu message
    if context.user_data.get('menu_message_id') is not None:
        print(context.user_data['menu_message_id'])
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=context.user_data['menu_message_id'])
    
    # Logic for receiving SMS
    keyboard = [
        [InlineKeyboardButton("📩 One-time message", callback_data='one_time_message')],
        [InlineKeyboardButton("📲 Rent Phone Number", callback_data='rent_number')],
        [InlineKeyboardButton("🔢 My Rented Numbers", callback_data='my_rented_numbers')],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data='menu')]
    ]   
    
    await update.message.reply_text(
        "🇺🇸 Access Real USA Phone Numbers.",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    
    
    
#####rental

# 1. Message saying that only 30 days rental is available 
# 2. ask for service name
# 3. order rental
# 4. end conversation and open my rented numbers


RENTAL_FAQ, ASK_FOR_NUMBER_TYPE, PROCESS_NUMBER_TYPE_CHOICE, VALIDATE_SERVICE, ASK_FOR_SERVICE, RENTAL_ORDER_SPECIFIC_CONFIRMATION, RENTAL_ORDER_FINAL, RENTAL_ORDER_NOT_LISTED_CONFIRMATION = range(8)

async def ask_for_number_type(update: Update, context: ContextTypes) -> int:
    
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        f"Choose an option from below.",
        reply_markup=InlineKeyboardMarkup(rental_choose_service_buttons)
    )
    
    # return PROCESS_NUMBER_TYPE_CHOICE

async def process_any_service_rental_choice(update: Update, context: ContextTypes) -> int:
    # query = update.callback_query
    # await query.answer()
    
    #set current rental type to any service by id: None - any service, 817 - not listed, X - specific service
    context.user_data['rental_service_id'] = None
    # context.user_data['rental_order_id'] = 6
    user_id = update.effective_user.id
    value = user_data_store[user_id] = {'rental_order_id': 6}
    print(user_data_store, "user_data_store")
    context.user_data['rental_service_name'] = 'Any service'
    
    await order_final(update, context)
    print(context.user_data['rental_service_id'])
    
# async def process_specific_service_rental_choice(update: Update, context: ContextTypes) -> int:
#     print('process_specific_service_rental_choice 2 ')
    
#     # query = update.callback_query
#     # await query.answer()
#     print('process_specific_service_rental_choice 2 ')
    
#     user_id = update.effective_user.id
#     value = user_data_store[user_id] = {'rental_order_id': 7}
#     print(user_data_store, "user_data_store")
#     print('specific_service_rental')
#     return await order_final(update, context)
    

async def order_final(update: Update, context: ContextTypes) -> int:
    print('any_service_order_final')

    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        f"Please wait while we're processing your order.",
    )
    
    # get callback query data
    rental_type = update.callback_query.data
    print(rental_type, 'rental_type')
    
    
    print(user_data_store, "user_data_store, order final")
    
    if firebase_conn.check_if_enough_balance(query.from_user.id, all_services_price):
        #order rental number for any service
        # print(context.user_data['rental_service_id'])
        user_id = update.effective_user.id
        print(user_data_store.get(user_id).get('rental_order_id'))
        print(user_data_store, "user_data_store")
        order_response  = await sms_pool.order_rental(user_data_store.get(update.effective_user.id).get('rental_order_id'), 30, context.user_data['rental_service_id'])
        if order_response['success'] == 1:
            # If successful, deduct 30$ from balance
            firebase_conn.decrease_balance(query.from_user.id, all_services_price)
            
            # Add rental number to database
                #prepare dict
            rental_data = {
                'number': order_response['phonenumber'],
                'expiry': datetime.utcfromtimestamp(order_response['expiry']).isoformat() + 'Z',
                'service_id': context.user_data['rental_service_id'],
                'service_name': context.user_data['rental_service_name'],
            }
            firebase_conn.add_rental(query.from_user.id, order_response['rental_code'], rental_data)
            
            
            
            await my_rented_numbers_callback(update, context)
            
            # return ConversationHandler.END
            
        else:
            #if not, send error message
            await query.edit_message_text(
                f"Error: Try again later.",
            )
            return await cancel(update, context)
    else:
        #if not, send error message
        await query.edit_message_text(
            f"Error: Not enough balance.",
        )
        return await cancel(update, context)
        

    
async def ask_for_service(update: Update, context: ContextTypes) -> int:
    print('ask_for_service')
    query = update.callback_query
    await query.answer()
    
    #NULL Data
    context.user_data['rental_service_id'] = None
    context.user_data['rental_service_name'] = None
    
    user_id = update.effective_user.id
    user_data_store[user_id] = {'rental_order_id': 7}
    
    
    
    ask_servie_message = await query.edit_message_text(
        "Enter the name of the service for which you want to rent a number:",
        reply_markup=InlineKeyboardMarkup(cancel_button)
    )
    
    context.user_data['rental_ask_service_name_message_id'] = ask_servie_message.message_id
    
    
    return VALIDATE_SERVICE

async def validate_service(update: Update, context: ContextTypes) -> int:

    print('validate_service')
    # save service name
    service_name_input = update.message.text.lower()
    print(service_name_input)
    
    #delete user input message
    await update.message.delete()
    
    if context.user_data.get('rental_ask_service_name_message_id') is not None:
        #delete previous message (ask for service)
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=context.user_data['rental_ask_service_name_message_id'])
    
    ##get service id
    all_services = await sms_pool.get_service_list()
    
    #get service ID if service name is in the list
    for service in all_services:
        if service_name_input in service['name'].lower():
            context.user_data['rental_service_id'] = service['ID']
            context.user_data['rental_service_name'] = service['name']
            break

    print(context.user_data['rental_service_id'], context.user_data['rental_service_name'])
          
    if context.user_data['rental_service_id'] is not None:
        print(context.user_data['rental_service_id'], context.user_data['rental_service_name'])
        # save service name in context
        await service_found(update, context)
    else:
        await service_not_found(update, context)

    return ConversationHandler.END





async def service_not_found(update: Update, context: ContextTypes) -> int:

    await update.message.reply_text(
        f"Service not found. You can try again.",
        # f"If you can't find the service you want to rent the number for, pelase choose 'Not listed'",
        reply_markup=InlineKeyboardMarkup(rental_service_not_found_buttons)
    )
    
    # context.user_data['rental_service_id'] = 817
    # return await ask_for_service(update, context)
    # return ASK_FOR_SERVICE
    
    # return RENTAL_ORDER_NOT_LISTED_CONFIRMATION
    

    
async def service_found(update: Update, context: ContextTypes) -> int:
    
    await update.message.reply_text(
        f"✅ Service found, *{context.user_data['rental_service_name']}* "
        f"It's price is {service_found_price} USD.",
        reply_markup=InlineKeyboardMarkup(rental_confirm_order_buttons),
        parse_mode=ParseMode.MARKDOWN
    )
    
    
    # return RENTAL_ORDER_SPECIFIC_CONFIRMATION

async def rental_order_confirmation(update: Update, context: ContextTypes) -> int:
    print('rental_order_confirmation')
    await my_rented_numbers_callback(update, context)
    
    
    # return ConversationHandler.END



async def cancel(update: Update, context: ContextTypes) -> int:
    """End the conversation."""
    print('cancel')
    
    query = update.callback_query
    await query.answer()
        
    
    # await query.message.delete()

    # await query.message.reply_text(
    #     "Canceled",
    # )
    await menu(update, context)
    
    # return ConversationHandler.END


    
# rental_conv = ConversationHandler(
#     entry_points=[CallbackQueryHandler(ask_for_number_type, pattern='^rent_number$')],
#     # conversation_timeout=30,  # Timeout after 5 minutes of inactivity
#     states={
#         PROCESS_NUMBER_TYPE_CHOICE: [CallbackQueryHandler(process_number_type_choice)],
#         ASK_FOR_SERVICE: [CallbackQueryHandler(ask_for_service, pattern='^specific_service_rental$')],
#         VALIDATE_SERVICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, validate_service)],
#         RENTAL_ORDER_FINAL: [CallbackQueryHandler(order_final, pattern='^confirm_order_any_service$')],
#         RENTAL_ORDER_SPECIFIC_CONFIRMATION: [CallbackQueryHandler(order_final, pattern='^confirm_order$')],
#         RENTAL_ORDER_NOT_LISTED_CONFIRMATION: [CallbackQueryHandler(order_final, pattern='^service_not_listed$')],
#     },
#     fallbacks=[
#         CallbackQueryHandler(cancel, pattern='^menu$')
#     ]
# )
    
rental_conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(ask_for_service, pattern='^specific_service_rental$')],
    states={
        VALIDATE_SERVICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, validate_service)]
    },
    fallbacks=[
        CallbackQueryHandler(cancel, pattern='^menu$')
    ]
)
    
    
    
