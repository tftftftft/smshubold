
import logging
import firebase_admin
from firebase_admin import db
from typing import TypeVar, Type, Optional
import os


logger = logging.getLogger(__name__)




# Generic type for model classes
T = TypeVar('T')

class FirebaseService:
    def __init__(self, database_url: str, credential_path: str):
        # Initialize Firebase app with credentials
        cred = firebase_admin.credentials.Certificate(credential_path)
        firebase_admin.initialize_app(cred, {'databaseURL': database_url})

    def add(self, ref: str, key: str, data: T) -> bool:
        """ Add data to the specified reference and key if it doesn't already exist. """

        # If the record does not exist, add it
        db.reference(f'{ref}/{key}').set(data.to_dict())
        return True

    def exists(self, ref: str, key: str) -> bool:
        """ Check if a record exists at the specified reference and key. """
        return db.reference(f'{ref}/{key}').get() is not None

    def update(self, ref: str, key: str, data: dict) -> None:
        """ Update data at the specified reference and key. """
        db.reference(f'{ref}/{key}').update(data)

    def get(self, ref: str, key: str) -> Optional[T]:
        """ Retrieve data from the specified reference and key. """
        data = db.reference(f'{ref}/{key}').get()
        return data
    
    def delete(self, ref: str, key: str) -> None:
        """ Delete data from the specified reference and key. """
        db.reference(f'{ref}/{key}').delete()
        
    def add_balance(self, user_id: str, amount: float) -> bool:
        """Add the specified amount to the user's balance."""

        # Define the reference and key for the user's balance
        ref = 'users'
        key = f'{user_id}/balance'

        # Retrieve the current balance
        current_balance = self.get(ref, key)
        if current_balance is None:
            print(f"User {user_id} not found or balance not set.")
            return False
        print(f"Current balance: {current_balance}")

        try:
            amount_float = float(amount)
        except ValueError:
            print(f"Amount {amount} is not a valid number.")
            return False

        # Calculate the new balance
        new_balance = current_balance + amount_float
        self.update(ref, user_id, {'balance': new_balance})

        return True
    
    def decrease_balance(self, user_id: str, amount: float) -> bool:
        """Decrease the specified amount from the user's balance."""

        # Define the reference and key for the user's balance
        ref = 'users'
        key = f'{user_id}/balance'

        # Retrieve the current balance
        current_balance = self.get(ref, key)
        if current_balance is None:
            print(f"User {user_id} not found or balance not set.")
            return False
        print(f"Current balance: {current_balance}")

        try:
            amount_float = float(amount)
        except ValueError:
            print(f"Amount {amount} is not a valid number.")
            return False

        # Calculate the new balance
        new_balance = current_balance - amount_float
        self.update(ref, user_id, {'balance': new_balance})

        return True
    
    def check_if_enough_balance(self, user_id: str, amount: float) -> bool:
        """Check if the user has enough balance for the specified amount."""
        
        # Define the reference and key for the user's balance
        ref = 'users'
        key = f'{user_id}/balance'

        # Retrieve the current balance
        current_balance = self.get(ref, key)
        if current_balance is None:
            print(f"User {user_id} not found or balance not set.")
            return False
        print(f"Current balance: {current_balance}")

        try:
            amount_float = float(amount)
        except ValueError:
            print(f"Amount {amount} is not a valid number.")
            return False
        
        if current_balance >= amount_float:
            return True
        else:
            return False



firebase_conn = FirebaseService(database_url=f'{os.getenv("FIREBASE_URL")}', credential_path=f'{os.getenv("FIREBASE_ACCESS_JSON_PATH")}')