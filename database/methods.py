
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
        try:
            # If the record does not exist, add it
            db.reference(f'{ref}/{key}').set(data)
            return True
        except Exception as e:
            logger.error(f'Error adding data to Firebase: {e}')
            return False

    def exists(self, ref: str, key: str) -> bool:
        """ Check if a record exists at the specified reference and key. """
        return db.reference(f'{ref}/{key}').get() is not None

    def update(self, ref: str, key: str, data: dict) -> None:
        """ Update data at the specified reference and key. """
        db.reference(f'{ref}/{key}').update(data)

    def get(self, ref: str, key: str) -> Optional[T]:
        """ Retrieve data from the specified reference and key. """
        try:
            data = db.reference(f'{ref}/{key}').get()
            return data
        except Exception as e:
            logger.error(f'Error retrieving data from Firebase: {e}')
            return None
        
    def delete(self, ref: str, key: str) -> None:
        """ Delete data from the specified reference and key. """
        try:
            db.reference(f'{ref}/{key}').delete()
        except Exception as e:
            logger.error(f'Error deleting data from Firebase: {e}')
            return None
        
    def get_user_balance(self, user_id: str) -> float:
        """Retrieve the user's balance."""
        
        # Define the reference and key for the user's balance
        ref = 'users'
        key = f'{user_id}/balance'
        
        # Retrieve the balance
        return self.get(ref, key)
        
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

    ### RENTAL METHODS ###
    def add_rental(self, user_id: str, rental_id: str, rental_data: dict) -> bool:
        """Add the rental data to the user's rental list."""
        
        # Define the reference and key for the user's rental list
        ref = 'users'
        key = f'{user_id}/rentals/{rental_id}'
        
        # Add the rental data
        return self.add(ref, key, rental_data)
    
    def get_rentals(self, user_id: str) -> dict:
        """Retrieve the user's rental list."""
        
        # Define the reference and key for the user's rental list
        ref = 'users'
        key = f'{user_id}/rentals'
        
        # Retrieve the rental list
        return self.get(ref, key)
    
    def get_rental_by_id(self, user_id: str, rental_id: str) -> dict:
        """Retrieve the rental data by rental ID."""
        
        # Define the reference and key for the user's rental list
        ref = 'users'
        key = f'{user_id}/rentals/{rental_id}'
        
        # Retrieve the rental data
        return self.get(ref, key)
    
    #delete rental number from user's rental list
    def delete_rental(self, user_id: str, rental_id: str) -> None:
        """Delete the rental data from the user's rental list."""
        
        # Define the reference and key for the user's rental list
        ref = 'users'
        key = f'{user_id}/rentals/{rental_id}'
        
        # Delete the rental data
        self.delete(ref, key)
        

    


firebase_conn = FirebaseService(database_url=f'{os.getenv("FIREBASE_URL")}', credential_path=f'{os.getenv("FIREBASE_ACCESS_JSON_PATH")}')