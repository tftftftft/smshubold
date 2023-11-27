from datetime import datetime
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import (
    ContextTypes,
)

from models.models import User

from database.methods import firebase_conn

keyboard = [
        ["Receive SMS"],  # First row with one button
        ["My Profile", "Technical Support"] # Second row with two buttons
    ]

# Start, show Greeting and an option to see the terms of use (button)
async def start(update: Update, context: ContextTypes) -> None:
    '''Start the conversation and offer options including terms of use, technical support, and profile access.'''

    username = update.message.from_user.username
    userid = update.message.from_user.id
    print(userid)
    # print(context.user_data['rental_type'])
    
    # Add user to database if it doesn't exist
    if firebase_conn.exists('users', userid) is False:
        user = User(balance=0)
        print(userid)
        firebase_conn.add('users', userid, user.to_dict())
    
    await update.message.reply_text(
        f"Hi {username}! I'm a bot that can help you to receive an SMS to a REAL USA phone number.\n\n"
        "Choose an option from below.",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True),
    )
    
async def menu(update: Update, context: ContextTypes) -> None:
    '''Show the menu again.'''
    print("menu")
    query = update.callback_query
    await query.answer()
    
    ###delete previous message
    # await query.message.delete()
    
    await query.message.reply_text(
        "Choose an option from below.",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True, is_persistent=True),
    )
    


###menu without deleting previous message
async def light_menu(update: Update, context: ContextTypes) -> None:
    '''Show the menu again.'''
    print("light menu")
    query = update.callback_query
    await query.answer()
     
    await query.message.reply_text(
        "Choose an option from below.",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True),
    )