from datetime import datetime
import asyncio
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    ContextTypes,
)

from bot.start.handler import menu


from services.smspool_objects import sms_pool
from database.methods import firebase_conn
    
    
async def my_rented_numbers_callback(update: Update, context: ContextTypes) -> None:
    query = update.callback_query
    await query.answer()

    
    rented_numbers = firebase_conn.get_rentals(query.from_user.id)
    
    if rented_numbers is not None:
    #check expiration of each number and delete from db those that are expired
        for key in list(rented_numbers.keys()):
            print(rented_numbers[key]['expiry'])
            days_left = (datetime.strptime(rented_numbers[key]['expiry'], '%Y-%m-%dT%H:%M:%SZ') - datetime.utcnow()).days
            if days_left < 0:
                firebase_conn.delete_rental(query.from_user.id, key)
                del rented_numbers[key]

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
        #add cancel button
        keyboard.append(
            [InlineKeyboardButton(f"🔙 Back to Menu", callback_data='menu')])

        reply_markup = InlineKeyboardMarkup(keyboard)

        # Send message with the inline keyboard
        await query.message.edit_text("📱 Your rented numbers:", reply_markup=reply_markup)
    else:
        await query.message.edit_text("🔙 You don't have any rented numbers.")
        await menu(update, context)
        return

async def rented_number_callback(update: Update, context: ContextTypes) -> None:
    query = update.callback_query
    await query.answer()

    # Extract the key from the callback data
    key = query.data.split('_')[-1]
    
    rental_number_data = firebase_conn.get_rental_by_id(query.from_user.id, key)
    status_response = await sms_pool.retrive_rental_status(key)
    status = status_response['status']['available'] == 1
    print(status_response)
    print(status_response['status']['available'])
    print(status)

    #{'success': 1, 'status': {'available': 1, 'phonenumber': '16084192881', 'activeFor': 270, 'expiry': 1703570373, 'auto_extend': 0}}
    print(status)
    #{'expiry': '2023-12-26T05:59:33Z', 'number': '16084192881', 'service_id': 329, 'service_name': 'Facebook'}
    print(rental_number_data)
    
    if rental_number_data is None:
        await query.message.reply_text(f"Error: Number not found Try again later.")
        await menu(update, context)
        return
    
    keyboard = [
        [InlineKeyboardButton(f"📩 Messages", callback_data=f'rental_messages_history_{key}')],
        [InlineKeyboardButton(f"🔍 Check status", callback_data=f'rented_number_{key}')],
        [InlineKeyboardButton(f"🔙 Back to Menu", callback_data='menu')]
    ]

    
    async def update_message(current_status: bool):
        status_update_text = ("🟢 Phone number is active and waiting for messages" if current_status else "🔴 Activating phone number, status updates every 3 minute.")

        status_text = "Active" if current_status else "Not active"
        
        #expiry': '2023-12-26T05:59:33Z'
        print(rental_number_data['expiry'])
        days_left = (datetime.strptime(rental_number_data['expiry'], '%Y-%m-%dT%H:%M:%SZ') - datetime.utcnow()).days

        await query.message.edit_text(
            f"🌟 <b>Rented Number:</b> +{rental_number_data['number']}\n"
            f"🔍 <b>For Service:</b> {rental_number_data['service_name'] if rental_number_data['service_name'] else 'Any Service'}\n"
            f"⏳ <b>Expires In:</b> {days_left} days\n\n"
            f"{status_update_text}\n",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.HTML
        )

    await update_message(status)

    
async def rental_history(update: Update, context: ContextTypes) -> None:
    
    query = update.callback_query
    await query.answer()
    
    # Extract the key from the callback data
    key = query.data.split('_')[-1]
    
    back_to_menu_button = [InlineKeyboardButton(f"🔙 Back to Menu", callback_data='menu')]
    
    response = await sms_pool.retrive_rental_messages(key)
    print(response)
    
    #if messages are not empty:
    if 'messages' in response and response['messages']:
        # Construct the message with all the messages
        message = ""
        for _, details in response['messages'].items():
            #if sender is not SMSPool, add it to the message
            if details['sender'] != 'SMSPool':
                message += f"📨 From: {details['sender']}\n"
                message += f"📝 Message: {details['message']}\n"
                message += f"⏰ Time: {details['timestamp']}\n\n"
            
        rental_messages_history=  await query.message.edit_text(
            message,
            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton(f"🔄 Update message list", callback_data=f"rental_messages_history_{key}")],
                back_to_menu_button
            ])
        ) 
        context.user_data['rental_messages_history_message_id'] = rental_messages_history.message_id  
    else:
        rental_messages_history= await query.message.edit_text(
            f"No messages found.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"🔙 Back to Menu", callback_data='menu')]])
            )
        context.user_data['rental_messages_history_message_id'] = rental_messages_history.message_id
        
    #spawn task to check for new messages
    # asyncio.create_task(check_for_new_rental_messages(key, update, context))




            

