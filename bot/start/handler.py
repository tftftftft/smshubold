from datetime import datetime
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import (
    ContextTypes,
)
import asyncio

from telegram.constants import ParseMode

from models.models import User

from database.methods import firebase_conn

keyboard = [
    ["📩 Receive SMS"],  # First row with one button
    ["👤 My Profile", "🔧 Technical Support"]  # Second row with two buttons
]

# Start, show Greeting and an option to see the terms of use (button)
async def start(update: Update, context: ContextTypes) -> None:
    '''Start the conversation and offer options including terms of use, technical support, and profile access.'''

    username = update.message.from_user.username
    userid = update.message.from_user.id
    print(userid)
    # print(context.user_data['rental_type'])
    
    # delete user's /start message if it is not first message in chat
    if context.user_data.get('start_message_id') is not None:
        await update.message.delete()
    
    # # delete start message
    # if context.user_data.get('start_message_id') is not None:
    #     print(context.user_data['start_message_id'])
    #     await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=context.user_data['start_message_id'])

    
    # Add user to database if it doesn't exist
    if firebase_conn.exists('users', userid) is False:
        user = User(balance=0)
        print(userid)
        firebase_conn.add('users', userid, user.to_dict())
        
    # Path to your local image file
    image_path = './files/logo.jpg'
        
    greeting_message = (
        f"🇺🇸 Welcome, @{username}! 🇺🇸\n"
        "📱 SMS verification with **REAL** USA numbers\n\n"
        "👇 Select available options below!"
    )
    
        # Send a photo with the message and inline keyboard
    with open(image_path, 'rb') as photo:
        start_messge_id = await update.message.reply_photo(
            photo=photo,
            caption=greeting_message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True, is_persistent=True),
        )
        
    #save message id to delete it later
    context.user_data['menu_message_id'] = start_messge_id.message_id
    

    
    
async def menu(update: Update, context: ContextTypes) -> None:
    '''Show the menu again.'''
    print("menu")
    query = update.callback_query
    await query.answer()
    
    ###delete previous message
    await query.message.delete()

    # if context.user_data.get('menu_message_id') is not None:
    #     print(context.user_data['menu_message_id'])
    #     await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=context.user_data['menu_message_id'])

    
    menu_message = await query.message.reply_text(
        "Choose an option from below.",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True, is_persistent=True),
    )
    
    context.user_data['menu_message_id'] = menu_message.message_id
    


###menu without deleting previous message
async def light_menu(update: Update, context: ContextTypes) -> None:
    '''Show the menu again.'''
    print("light menu")
    query = update.callback_query
    await query.answer()
     
    menu_message = await query.message.reply_text(
        "Choose an option from below.",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True, is_persistent=True),
    )
    
    context.user_data['menu_message_id'] = menu_message.message_id