from datetime import datetime
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import (
    ContextTypes,
)

from models import User

from main import db



# Start, show Greeting and an option to see the terms of use (button)
async def start(update: Update, context: ContextTypes) -> None:
    '''Start the conversation and offer options including terms of use, technical support, and profile access.'''

    username = update.message.from_user.username
    userid = update.message.from_user.id
    keyboard = [
        ["Receive SMS"],  # First row with one button
        ["My Profile", "Technical Support"] # Second row with two buttons
    ]
    
    # Add user to database if it doesn't exist
    if db.exists is not False:
        user = User(balance=0)
        db.add('users', 'user_id', user)
    
    await update.message.reply_text(
        f"Hi {username}! I'm a bot that can help you to receive an SMS to a REAL USA phone number.\n\n"
        "Choose an option from below.",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=False, resize_keyboard=True),
    )