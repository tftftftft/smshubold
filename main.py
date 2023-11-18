import logging
from typing import Dict
import os
from dotenv import load_dotenv
load_dotenv()  # This loads the variables from .env


from bot.support.handler import technical_support
from bot.sms.handler import receive_sms, one_time_message_callback, unlimited_messages_callback, my_rented_numbers_callback
from bot.profile.handler import my_profile, add_balance_callback
from bot.start.handler import start


from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,

)




# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged


logger = logging.getLogger(__name__)



def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.

    logger.info("Starting bot")

    application = Application.builder().token(os.getenv("BOT_TOKEN")).build()
    
    
    application.add_handler(CommandHandler("start", start))
    
    application.add_handler(MessageHandler(filters.Regex("^Receive SMS$"), receive_sms))
    application.add_handler(MessageHandler(filters.Regex("^My Profile$"), my_profile))
    application.add_handler(MessageHandler(filters.Regex("^Technical Support$"), technical_support))

    
    #profile callback
    application.add_handler(CallbackQueryHandler(add_balance_callback, pattern='^add_balance$'))
    
    # sms callbacks
    application.add_handler(CallbackQueryHandler(one_time_message_callback, pattern='^one_time_message$'))
    application.add_handler(CallbackQueryHandler(unlimited_messages_callback, pattern='^unlimited_messages$'))
    application.add_handler(CallbackQueryHandler(my_rented_numbers_callback, pattern='^my_rented_numbers$'))
    
    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
