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


from services.smspool_objects import sms_pool
from database.methods import firebase_conn

service_found_price = 15
service_not_found_price = 20
all_services_price = 30

##817 service id for not listed

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
    # [InlineKeyboardButton("Service not listed - 15$", callback_data='service_not_listed')],
    [InlineKeyboardButton("Try again", callback_data='specific_service_rental')],
    [InlineKeyboardButton("Cancel", callback_data='cancel_action')] 
]

rental_confirm_order_buttons = [
    [InlineKeyboardButton("Confirm", callback_data='confirm_order')],
    [InlineKeyboardButton("Cancel", callback_data='cancel_action')]
]

rental_any_service_order_confirmation_buttons = [
    [InlineKeyboardButton("Confirm", callback_data='confirm_order_any_service')],
    [InlineKeyboardButton("Cancel", callback_data='cancel_action')]
]

# rental_final_buttons = [
#     [InlineKeyboardButton("Go to rentals", callback_data='my_rented_numbers')],
#     [InlineKeyboardButton("Back to Menu", callback_data='menu')]
# ]

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


RENTAL_FAQ, ASK_FOR_NUMBER_TYPE, PROCESS_NUMBER_TYPE_CHOICE, VALIDATE_SERVICE, ASK_FOR_SERVICE, RENTAL_ORDER_SPECIFIC_CONFIRMATION, RENTAL_ORDER_FINAL, RENTAL_ORDER_NOT_LISTED_CONFIRMATION = range(8)

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
    
async def process_number_type_choice(update: Update, context: ContextTypes) -> int:    
    query = update.callback_query
    await query.answer()

    # Get the user's choice
    choice = query.data
    print(choice)
    if choice == 'any_service_rental':
        #set current rental type to any service by id: None - any service, 817 - not listed, X - specific service
        context.user_data['service_id'] = None
        context.user_data['id'] = 6
        # If user chooses "Any service", go to rental_order_confirmation
        return await order_final(update, context)

    elif choice == 'specific_service_rental':
        context.user_data['id'] = 7
        # If user chooses "Specific service", go to ask_for_service
        print('specific_service_rental')
        return await ask_for_service(update, context)


async def order_final(update: Update, context: ContextTypes) -> int:
    print('any_service_order_final')
    #check if enough balance
    #order rental number for any service
    #if successfull, deduct 30$ from balance
    #if not, send error message
    #show message with number and expiration date, activate phone number
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        f"Please wait while we're processing your order.",
    )
    
    if firebase_conn.check_if_enough_balance(query.from_user.id, all_services_price):
        #order rental number for any service
        print(context.user_data['service_id'])
        order_response  = sms_pool.order_rental(context.user_data['id'], 30, context.user_data['service_id'])
        if order_response['success'] == 1:
            # If successful, deduct 30$ from balance
            firebase_conn.decrease_balance(query.from_user.id, all_services_price)
            
            # Add rental number to database
            #prepare dict
            rental_data = {
                'number': order_response['phonenumber'],
                'expiry': datetime.utcfromtimestamp(order_response['expiry']).isoformat() + 'Z',
                'service_id': context.user_data['service_id'],
                'service_name': context.user_data['service_name_rental'],
            }
            firebase_conn.add_rental(query.from_user.id, order_response['rental_code'], rental_data)
            
            # Show message with number and expiration date, activate phone number
            message = f"Please wait for 3 minutes for the number to be activated.\n"
            message = f"Your rental number is {order_response['phonenumber']}.\n"
            if context.user_data['service_name_rental']:
                message += f"For service: {context.user_data['service_name_rental']}.\n"
            else:
                message += f"For any service.\n"
            message += f"It will expire on {datetime.fromtimestamp(order_response['expiry'])}.\n"
            
            
            await query.edit_message_text(
                message,                    
            )
            
            #redirect to my rented numbers
            # await query.message.reply_text(
            #     f"You are being redirected to My Rented Numbers.",
            # )
            
            await my_rented_numbers_callback(update, context)
            
            return ConversationHandler.END
            
            # ###wait for sms
            # rental_code = order_response['rental_code']

            # while True:
            #     print('while')
            #     await asyncio.sleep(5)

            #     check_response = sms_pool.retrive_rental_messages(rental_code)
            #     print(check_response)
            #     # {'success': 1, 'messages': {'0': {'ID': 4, 'sender': '32665', 'message': '44587 ds din bekrdgtelsekod freo Facebook', 'timestamp': '2023-11-26 04:48:41'}, '1': {'ID': 3, 'sender': '32665', 'message': '75691 adalah kode konfirmasi Facebook Anda', 'timestamp': '2023-11-26 04:48:35'}, '2': {'ID': 2, 'sender': '32665', 'message': '44587 ds din bekrdgtelsekod freo Facebook', 'timestamp': '2023-11-26 04:48:33'}}, 'source': 11}
            #     if check_response['messages'] is not None:
                    
                
                
        else:
            #if not, send error message
            await query.edit_message_text(
                f"Error: Try again later.",
            )
    else:
        #if not, send error message
        await query.edit_message_text(
            f"Error: Not enough balance.",
        )
        
    return ConversationHandler.END
    
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
    service_name_input = update.message.text.lower()
    print(service_name_input)
    
    ##get service id
    
    all_services = sms_pool.get_service_list()
    
    #get service ID if service name is in the list
    for service in all_services:
        if service['name'].lower() == service_name_input:
            context.user_data['service_id'] = service['ID']
            context.user_data['service_name_rental'] = service['name']
            break

    print(context.user_data['service_id'], context.user_data['service_name_rental'])
          
    if context.user_data['service_id'] is not None:
        print(context.user_data['service_id'], context.user_data['service_name_rental'])
        # save service name in context
        return await service_found(update, context)
    else:
        return await service_not_found(update, context)






async def service_not_found(update: Update, context: ContextTypes) -> int:

    await update.message.reply_text(
        f"Service not found. You can try again.",
        # f"If you can't find the service you want to rent the number for, pelase choose 'Not listed'",
        reply_markup=InlineKeyboardMarkup(rental_service_not_found_buttons)
    )
    
    # context.user_data['service_id'] = 817
    # return await ask_for_service(update, context)
    return ASK_FOR_SERVICE
    
    # return RENTAL_ORDER_NOT_LISTED_CONFIRMATION
    

    
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
    
    # await query.message.delete()

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
        RENTAL_ORDER_FINAL: [CallbackQueryHandler(order_final, pattern='^confirm_order_any_service$')],
        RENTAL_ORDER_SPECIFIC_CONFIRMATION: [CallbackQueryHandler(order_final, pattern='^confirm_order$')],
        RENTAL_ORDER_NOT_LISTED_CONFIRMATION: [CallbackQueryHandler(order_final, pattern='^service_not_listed$')],
    },
    fallbacks=[
        CallbackQueryHandler(cancel, pattern='^cancel_action$')
    ]
)
    

    
    
    
###############
#Rented numbers    
    

    # check if user has rented numbers in the database
    # if yes, show them as a buttons with inline keyboard
    # if no, show message saying that there are no rented numbers
    # show cancel button
    
    #when user clicks on the button, show the number info.
        #show buttons: messages history, button to check if number is active, cancel
        #if active - start accepting messages
    
    
async def my_rented_numbers_callback(update: Update, context: ContextTypes) -> None:
    query = update.callback_query
    await query.answer()

    
    rented_numbers = firebase_conn.get_rentals(query.from_user.id)

    # Check if user has rented numbers
    if not rented_numbers:
        await query.message.edit_text("You don't have any rented numbers.")
        await menu(update, context)
        return 

    # Create a list of InlineKeyboardButton, one for each rented number
    keyboard = []
    for key, details in rented_numbers.items():
        button_text = f"+{details['number']} - {details['service_name'] if details['service_name'] else 'Any service'}"
        callback_data = f"rented_number_{key}"  # Use the unique key as callback data
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send message with the inline keyboard
    await query.message.edit_text("Your rented numbers:", reply_markup=reply_markup)

async def rented_number_callback(update: Update, context: ContextTypes) -> None:
    query = update.callback_query
    await query.answer()

    # Extract the key from the callback data
    key = query.data.split('_')[-1]
    
    rental_number_data = firebase_conn.get_rental_by_id(query.from_user.id, key)
    status = sms_pool.retrive_rental_status(key)['status']['available'] == 1
    # status = False # test

    #{'success': 1, 'status': {'available': 1, 'phonenumber': '16084192881', 'activeFor': 270, 'expiry': 1703570373, 'auto_extend': 0}}
    print(status)
    #{'expiry': '2023-12-26T05:59:33Z', 'number': '16084192881', 'service_id': 329, 'service_name': 'Facebook'}
    print(rental_number_data)
    
    if rental_number_data is None:
        await query.message.reply_text(f"Error: Number not found.")
        await menu(update, context)
        return
    
    keyboard = [
        [InlineKeyboardButton("Messages", callback_data=f'rental_messages_history_{key}')],
        [InlineKeyboardButton("Back to Menu", callback_data='menu')]
    ]

    
    async def update_message(current_status: bool):
        status_update_text = ("Phone number is active and listening for messages" if current_status else "Activating phone number, status updates every 3 minute.")

        status_text = "Active" if current_status else "Not active"

        await query.message.edit_text(
            f"Your rented number is +{rental_number_data['number']}.\n"
            f"For service: {rental_number_data['service_name'] if rental_number_data['service_name'] else 'Any service'}.\n"
            f"It will expire on {rental_number_data['expiry']}.\n"
            f"{status_update_text}\n"
            f"Status: {status_text}.\n",
            reply_markup=InlineKeyboardMarkup(keyboard)
    )

    await update_message(status)
    
    #every 3 minute check if number is active
    #if active, update message
    #if not, update message
    # while True:
    #     await asyncio.sleep(100)
    #     status = sms_pool.retrive_rental_status(key)
    #     if status['status']['available'] == 1:
    #         await update_message(status)
    #         break
    async def check_status_periodically():
        while True:
            print('check_status_periodically')
            await asyncio.sleep(10)  # Wait for 3 minutes (180 seconds) between checks
            if sms_pool.retrive_rental_status(key)['status']['available'] == 1:
                await update_message(True)
                break
                
    asyncio.create_task(check_status_periodically())
            

    
async def rental_history(update: Update, context: ContextTypes) -> None:
    
    query = update.callback_query
    await query.answer()
    
    # Extract the key from the callback data
    key = query.data.split('_')[-1]
    
    response = sms_pool.retrive_rental_messages(key)
    print(response)
    
    if response['messages'] is None:
        await query.message.reply_text(f"No messages found.")
        await menu(update, context)
        return
    
    # Construct the message with all the messages
    message = ""
    for key, details in response['messages'].items():
        message += f"From: {details['sender']}\n"
        message += f"Message: {details['message']}\n"
        message += f"Time: {details['timestamp']}\n\n"
        
    await query.message.reply_text(
        message,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back to Menu", callback_data='menu')]])
    ) 
    
