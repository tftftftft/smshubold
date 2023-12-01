import logging
from typing import Dict
import os
import threading
from dotenv import load_dotenv
load_dotenv()  # This loads the variables from .env


from bot.support.handler import technical_support
from bot.sms.handler import receive_sms, my_rented_numbers_callback, rental_conv
from bot.sms.rent_history import  rented_number_callback, rental_history
from bot.sms.otp_handler import ask_for_service_name, otp_confirmation, order_phone_number_otp, resend_otp, cancel
# from bot.profile.handler import my_profile, add_balance_callback
from bot.profile.handler import my_profile, process_crypto, ask_amount
from bot.start.handler import start, menu

from services.smspool_objects import sms_pool
from services.cryptomus.cryptomus_objects import cryptomus
from services.cryptomus.flask_listeners import app

from database.methods import firebase_conn



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

def run_flask_app():
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)

def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.

    logger.info("Starting bot")
    
    threading.Thread(target=run_flask_app).start()
  
    application = Application.builder().token(os.getenv("BOT_TOKEN")).build()
    

    application.add_handler(CommandHandler("start", start))
    
    application.add_handler(CallbackQueryHandler(menu, pattern='^menu$'))
        
    application.add_handler(MessageHandler(filters.Regex("^📩 Receive SMS$"), receive_sms))
    application.add_handler(MessageHandler(filters.Regex("^👤 My Profile$"), my_profile))
    application.add_handler(MessageHandler(filters.Regex("^🔧 Technical Support$"), technical_support))

    
    #profile callback
    # application.add_handler(CallbackQueryHandler(add_balance_callback, pattern='^add_balance$'))
    # application.add_handler(deposit_conv)
    application.add_handler(CallbackQueryHandler(ask_amount, pattern='^deposit$'))
    application.add_handler(CallbackQueryHandler(process_crypto, pattern='^(10|20|50|100|200|500)$'))
    
    #otp convo
    # application.add_handler(otp_conv)
    
    #rental convo
    application.add_handler(rental_conv)
        
    # sms callbacks
    application.add_handler(CallbackQueryHandler(my_rented_numbers_callback, pattern='^my_rented_numbers$'))
    application.add_handler(CallbackQueryHandler(rental_history, pattern='^rental_messages_history_.*$'))
    application.add_handler(CallbackQueryHandler(rented_number_callback, pattern='^rented_number_.*$'))
    
    #test
    application.add_handler(CallbackQueryHandler(ask_for_service_name, pattern='^one_time_message$'))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, otp_confirmation))
    application.add_handler(CallbackQueryHandler(order_phone_number_otp, pattern='^yes_confirmation_otp$'))
    application.add_handler(CallbackQueryHandler(resend_otp, pattern='^resend_otp$')),
    application.add_handler(CallbackQueryHandler(cancel, pattern='^cancel_action$')),
    application.add_handler(CallbackQueryHandler(cancel, pattern='^no_confirmation_otp$'))
    
    
    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
