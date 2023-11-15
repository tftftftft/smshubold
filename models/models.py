from datetime import datetime
from typing import Optional, Dict, Union

class Invoice:
    def __init__(self, amount_in_usd: float, amount_in_crypto: float, currency: str, crypto_address: str, status: str):
        self.amount_in_usd = amount_in_usd
        self.amount_in_crypto = amount_in_crypto
        self.currency = currency
        self.crypto_address = crypto_address
        self.timestamp = datetime.utcnow().isoformat() + 'Z'
        self.status = status

class OrderOTP:
    def __init__(self, price: float, phone_number: str, status: str, refunded: Optional[bool] = None):
        self.price = price
        self.phone_number = phone_number
        self.timestamp = datetime.utcnow().isoformat() + 'Z'
        self.status = status
        self.refunded = refunded

class OrderRental:
    def __init__(self, price: float, phone_number: str, rental_period: int, status: str, refunded: Optional[bool] = None):
        self.price = price
        self.phone_number = phone_number
        self.timestamp = datetime.utcnow().isoformat() + 'Z'
        self.rental_period = rental_period
        self.status = status
        self.refunded = refunded

class User:
    def __init__(self, balance: float):
        self.status = 'active'
        self.balance = balance
        self.created_at = datetime.utcnow().isoformat() + 'Z'
        self.modified_at = self.created_at
        self.deleted_at = None
        self.invoices: Dict[str, Invoice] = {}
        self.otp_orders: Dict[str, OrderOTP] = {}
        self.rental_orders: Dict[str, OrderRental] = {}

    def add_invoice(self, key: str, invoice: Invoice):
        self.invoices[key] = invoice

    def add_order_otp(self, key: str, order_otp: OrderOTP):
        self.otp_orders[key] = order_otp

    def add_order_rental(self, key: str, order_rental: OrderRental):
        self.rental_orders[key] = order_rental

    def to_dict(self) -> dict:
        return {
            'status': self.status,
            'balance': self.balance,
            'created_at': self.created_at,
            'modified_at': self.modified_at,
            'deleted_at': self.deleted_at,
            'invoices': {k: v.__dict__ for k, v in self.invoices.items()},
            'otp_orders': {k: v.__dict__ for k, v in self.otp_orders.items()},
            'rental_orders': {k: v.__dict__ for k, v in self.rental_orders.items()}
        }
