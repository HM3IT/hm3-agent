from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from datetime import date


Category = Literal[
    "Taxi",
    "Food",
    "Drink",
    "Online Shopping",
    "Groceries",
    "Transport",
    "Health",
    "Entertainment",
    "Utilities",
    "Education",
    "Accommodation",
    "Other",
]



class ManualExpenseItem(BaseModel):
    category: Category = Field(
        description="Best matching expense category."
    )
    amount: float = Field(
        description="Amount paid in Thai Baht. Must be greater than zero.",
    )
    description: str = Field(
        description="Short description of the expense."
    )
    merchant: Optional[str] = Field(
        default=None,
        description="Merchant or place, if mentioned.",
    )

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("Expense amount must be greater than zero.")
        return value


class ManualExpenseResult(BaseModel):
    expenses: list[ManualExpenseItem] = Field(
        description="All separate expenses found in the message.",
    )


class ReceiptData(BaseModel):
    merchant: str = Field(description="Merchant, shop, restaurant, app, or service name.")
    transaction_date: str = Field(
        description="Purchase date in YYYY-MM-DD format. Use the visible receipt date."
    )
    transaction_time: Optional[str] = Field(
        default=None, description="Purchase time in HH:MM 24-hour format, if visible."
    )
    total_amount: float = Field(
       description="Final amount actually paid, after discounts and including tax. Must be greater than zero.",
    )
    currency: Literal["THB"] = Field(
        default="THB",
        description="Currency is always Thai Baht.",
    )
    category: Category = Field(description="Best single spending category.")
    item_description: str = Field(
        description="Short summary of the goods or service purchased."
    )
    payment_method: Optional[str] = Field(
        default=None, description="Cash, card, wallet, bank transfer, or other method if visible."
    )
    receipt_number: Optional[str] = Field(
        default=None, description="Receipt, invoice, or order number if visible."
    )
    tax_amount: Optional[float] = Field(
        default=None, ge=0, description="Tax amount if explicitly visible."
    )
    confidence: float = Field(
        ge=0,
        le=1,
        description="Confidence that the extracted merchant, date, total, and currency are correct.",
    )
    notes: Optional[str] = Field(
        default=None,
        description="Important uncertainty, unreadable information, refund status, or other note.",
    )

    @field_validator("transaction_date")
    @classmethod
    def validate_date(cls, value: str) -> str:
        date.fromisoformat(value)
        return value
    

    @field_validator("total_amount")
    @classmethod
    def validate_amount(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("Total amount must be greater than zero.")
        return value