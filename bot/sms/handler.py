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

from bot.start.handler import menu

service_found_price = 15
service_not_found_price = 20
all_services_price = 30

from services.smspool_objects import sms_pool

cancel_button = [
    [InlineKeyboardButton("Cancel", callback_data='cancel_action')]
]

rental_faq_buttons = [
    [InlineKeyboardButton("Continue", callback_data='continue_rental_1')],
    [InlineKeyboardButton("Cancel", callback_data='cancel_action')]
]

rental_choose_service_buttons = [
    [InlineKeyboardButton("Any service - 30$", callback_data='any_service_rental')],
    [InlineKeyboardButton("Specific service - 10$", callback_data='specific_service_rental')]
]

rental_service_not_found_buttons = [
    [InlineKeyboardButton("Service not listed - 15$", callback_data='service_not_listed')],
    [InlineKeyboardButton("Cancel", callback_data='cancel_action')] 
]

rental_confirm_order_buttons = [
    [InlineKeyboardButton("Confirm", callback_data='confirm_order')],
    [InlineKeyboardButton("Cancel", callback_data='cancel_action')]
]

async def receive_sms(update: Update, context: ContextTypes) -> None:
    # Logic for receiving SMS
    keyboard = [
        [InlineKeyboardButton("One-time message", callback_data='one_time_message')],
        [InlineKeyboardButton("Rent Phone Number", callback_data='rent_number')],
        [InlineKeyboardButton("My Rented Numbers", callback_data='my_rented_numbers')],
        [InlineKeyboardButton("Back to Menu", callback_data='menu')]
    ]
    
    await update.message.reply_text(
        "Choose an option from below.",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    
    
    
#####rental

# 1. Message saying that only 30 days rental is available 
# 2. ask for service name
# 3. order rental
# 4. end conversation and open my rented numbers


RENTAL_FAQ, ASK_FOR_NUMBER_TYPE, PROCESS_NUMBER_TYPE_CHOICE, VALIDATE_SERVICE, ASK_FOR_SERVICE, RENTAL_ORDER_SPECIFIC_CONFIRMATION, ANY_SERVICE_ORDER_CONFIRMATION, RENTAL_ORDER_NOT_LISTED_CONFIRMATION = range(8)

async def rental_faq(update: Update, context: ContextTypes) -> int:
    
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        f"Only 30 days rental is available for any service.",
        reply_markup=InlineKeyboardMarkup(rental_faq_buttons)
    )
    
    return ASK_FOR_NUMBER_TYPE


async def ask_for_number_type(update: Update, context: ContextTypes) -> int:
    
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        f"Choose an option from below.",
        reply_markup=InlineKeyboardMarkup(rental_choose_service_buttons)
    )
    
    return PROCESS_NUMBER_TYPE_CHOICE
    
async def process_number_type_choice(update: Update, context: ContextTypes) -> None:    
    query = update.callback_query
    await query.answer()

    # Get the user's choice
    choice = query.data
    print(choice)
    if choice == 'any_service_rental':
        #order rental number for any service
        
        # If user chooses "Any service", go to rental_order_confirmation
        return await rental_order_confirmation(update, context)

    elif choice == 'specific_service_rental':
        # If user chooses "Specific service", go to ask_for_service
        print('specific_service_rental')
        return await ask_for_service(update, context)

    
    
    
    
async def ask_for_service(update: Update, context: ContextTypes) -> int:
    print('ask_for_service')
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        f"Please enter the service name you want to rent the number for.",
        reply_markup=InlineKeyboardMarkup(cancel_button)
    )
    
    return VALIDATE_SERVICE

async def validate_service(update: Update, context: ContextTypes) -> int:

    print('validate_service')
    # save service name
    service_name_input = update.message.text
    print(service_name_input)
    
    # save service name in context
    context.user_data['service_name_rental'] = service_name_input
    
    response = sms_pool.get_service_price('US', service_name_input)
    print(response)
          
    if response['price'] is None:
        return await service_not_found(update, context)
    else:
        return await service_found(update, context)





async def service_not_found(update: Update, context: ContextTypes) -> int:

    await update.message.reply_text(
        f"Service not found."
        f"If you can't find the service you want to rent the number for, pelase choose 'Not listed'",
        reply_markup=InlineKeyboardMarkup(rental_service_not_found_buttons)
    )
    
    return RENTAL_ORDER_NOT_LISTED_CONFIRMATION
    

    
async def service_found(update: Update, context: ContextTypes) -> int:
    
    await update.message.reply_text(
        f"Service found. {context.user_data['service_name_rental']} "
        f"It's price is {service_found_price} USD.",
        reply_markup=InlineKeyboardMarkup(rental_confirm_order_buttons)   
    )
    
    return RENTAL_ORDER_SPECIFIC_CONFIRMATION

async def rental_order_confirmation(update: Update, context: ContextTypes) -> int:
    print('rental_order_confirmation')
    await my_rented_numbers_callback(update, context)
    
    
    return ConversationHandler.END



async def cancel(update: Update, context: ContextTypes) -> int:
    """End the conversation."""
    print('cancel')
    
    query = update.callback_query
    await query.answer()
        
    await query.message.reply_text(
        "Canceled",
    )

    await menu(update, context)
    
    return ConversationHandler.END


    
rental_conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(rental_faq, pattern='^rent_number$')],
    # conversation_timeout=30,  # Timeout after 5 minutes of inactivity
    states={
        ASK_FOR_NUMBER_TYPE: [CallbackQueryHandler(ask_for_number_type, pattern='^continue_rental_1$')],
        PROCESS_NUMBER_TYPE_CHOICE: [CallbackQueryHandler(process_number_type_choice)],
        ASK_FOR_SERVICE: [CallbackQueryHandler(ask_for_service, pattern='^specific_service_rental$')],
        VALIDATE_SERVICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, validate_service)],
        ANY_SERVICE_ORDER_CONFIRMATION: [CallbackQueryHandler(rental_order_confirmation, pattern='^any_service_rental$')],
        RENTAL_ORDER_SPECIFIC_CONFIRMATION: [CallbackQueryHandler(rental_order_confirmation, pattern='^confirm_order$')],
        RENTAL_ORDER_NOT_LISTED_CONFIRMATION: [CallbackQueryHandler(rental_order_confirmation, pattern='^service_not_listed$')],
    },
    fallbacks=[
        CallbackQueryHandler(cancel, pattern='^cancel_action$')
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