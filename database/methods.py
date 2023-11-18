
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

    def get(self, ref: str, key: str, cls: Type[T]) -> Optional[T]:
        """ Retrieve data from the specified reference and key. """
        data = db.reference(f'{ref}/{key}').get()
        if data:
            return cls(**data)
        return None

    def delete(self, ref: str, key: str) -> None:
        """ Delete data from the specified reference and key. """
        db.reference(f'{ref}/{key}').delete()



firebase_conn = FirebaseService(database_url=f'{os.getenv("FIREBASE_URL")}', credential_path=f'{os.getenv("FIREBASE_ACCESS_JSON_PATH")}')