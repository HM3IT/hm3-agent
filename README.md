# AI Finance Tracker

An AI-powered personal finance tracker that records expenses from Telegram messages and receipt images.

The application uses Google Gemini to understand natural-language expense messages and extract structured information from receipts. Expense records are validated, categorized, and stored in an Excel spreadsheet for later review and analysis.

## Features

* Record expenses through a Telegram bot
* Understand natural-language expense messages
* Parse receipt images using AI
* Extract expense information such as:

  * Merchant name
  * Transaction date
  * Total amount
  * Currency
  * Expense category
  * Purchased items
* Automatically categorize expenses
* Store financial records in an Excel workbook
* Handle incomplete or invalid expense information
* Log processing errors for debugging
* Support both manual expense entry and receipt-based entry

## Example Usage

### Manual expense entry

Send a message to the Telegram bot:

```text
I spent 250 THB on lunch today.
```

The application converts the message into structured data:

```json
{
  "amount": 250,
  "currency": "THB",
  "category": "Food",
  "description": "Lunch",
  "date": "2026-06-07"
}
```

### Receipt upload

Upload a receipt image to the Telegram bot.

The receipt parser analyzes the image and extracts information such as:

```json
{
  "merchant": "Example Restaurant",
  "date": "2026-06-07",
  "total_amount": 420,
  "currency": "THB",
  "category": "Food",
  "items": [
    {
      "name": "Chicken rice",
      "quantity": 2,
      "price": 360
    },
    {
      "name": "Water",
      "quantity": 2,
      "price": 60
    }
  ]
}
```

The extracted expense is then saved to the financial usage spreadsheet.

## Project Structure

```text
hm3-agent/
├── data/
│   └── financial_usage.xlsx
│
├── features/
│   ├── command_handler.py
│   ├── manual_expense_handler.py
│   ├── receipt_parser.py
│   └── expense_storage.py
│
├── config/
│   └── settings.py
│
├── logs/
│
├── tests/
│
├── .env
├── .env.example
├── .gitignore
├── main.py
├── pyproject.toml
├── README.md
└── uv.lock
```

The exact structure may differ depending on the current implementation.

## Main Components

### Telegram Command Handler

The command handler receives Telegram updates and determines how each request should be processed.

It can route:

* Text messages to the manual expense analyzer
* Receipt images to the receipt parser
* Bot commands to their corresponding handlers

Example location:

```text
features/command_handler.py
```

### Manual Expense Analyzer

The manual expense analyzer sends natural-language expense messages to Gemini and converts the response into structured expense data.

Example location:

```text
features/manual_expense_handler.py
```

### Receipt Parser

The receipt parser processes uploaded receipt images and extracts financial information.

It should:

1. Validate the uploaded image.
2. Send the image and extraction instructions to Gemini.
3. Parse the AI response.
4. Validate the extracted fields.
5. Convert the result into the internal expense model.
6. Save the expense to the spreadsheet.
7. Return a confirmation message to the Telegram user.

### Expense Storage

The storage layer writes validated expense records to:

```text
data/financial_usage.xlsx
```

A typical spreadsheet may contain these columns:

| Field       | Description                 |
| ----------- | --------------------------- |
| Date        | Date of the expense         |
| Merchant    | Merchant or store name      |
| Description | Expense description         |
| Category    | Expense category            |
| Amount      | Transaction amount          |
| Currency    | Transaction currency        |
| Source      | Manual entry or receipt     |
| Items       | Purchased items             |
| Created At  | Time the record was created |

## Technology Stack

* Python
* Telegram Bot API
* Google Gemini API
* Google GenAI Python SDK
* Pydantic
* OpenPyXL
* `uv` for package and environment management
* Excel for local financial data storage

## Requirements

Before running the project, make sure you have:

* Python 3.11 or later
* A Telegram bot token
* A Google Gemini API key
* `uv` installed

Install `uv`:

```bash
pip install uv
```

You can also follow the official `uv` installation method for your operating system.

## Installation

Clone the repository:

```bash
git clone <repository-url>
cd hm3-agent
```

Create the virtual environment and install dependencies:

```bash
uv sync
```

Activate the virtual environment on Windows:

```bash
.venv\Scripts\activate
```

Activate it on macOS or Linux:

```bash
source .venv/bin/activate
```

## Environment Configuration

Create a `.env` file in the project root:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash
FINANCIAL_DATA_PATH=data/financial_usage.xlsx
LOG_LEVEL=INFO
```

Do not commit the `.env` file to Git.

Add it to `.gitignore`:

```gitignore
.env
.venv/
__pycache__/
*.pyc
logs/
```

An `.env.example` file can be committed:

```env
TELEGRAM_BOT_TOKEN=
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.5-flash
FINANCIAL_DATA_PATH=data/financial_usage.xlsx
LOG_LEVEL=INFO
```

## Running the Application

Run the project with:

```bash
uv run python main.py
```

Alternatively, after activating the virtual environment:

```bash
python main.py
```

After the bot starts, open Telegram and send a message or upload a receipt image.

## Supported Expense Categories

The application may classify expenses into categories such as:

* Food
* Transport
* Shopping
* Bills
* Entertainment
* Health
* Education
* Travel
* Housing
* Subscription
* Personal care
* Other

Categories should be normalized before storing the expense.

For example:

```text
restaurant → Food
taxi → Transport
electricity bill → Bills
medicine → Health
```

## Expense Data Model

A possible Pydantic model for expense records is:

```python
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class ExpenseItem(BaseModel):
    name: str
    quantity: float | None = None
    price: Decimal | None = None


class ExpenseRecord(BaseModel):
    date: date
    amount: Decimal = Field(gt=0)
    currency: str
    category: str
    description: str
    merchant: str | None = None
    items: list[ExpenseItem] = []
    source: str
```

All AI-generated values should be validated before being saved.

## Processing Flow

### Manual expense flow

```text
Telegram text message
        ↓
Command handler
        ↓
Manual expense analyzer
        ↓
Gemini structured extraction
        ↓
Pydantic validation
        ↓
Excel storage
        ↓
Telegram confirmation
```

### Receipt processing flow

```text
Telegram receipt image
        ↓
Image download
        ↓
Receipt parser
        ↓
Gemini multimodal analysis
        ↓
Structured data extraction
        ↓
Pydantic validation
        ↓
Excel storage
        ↓
Telegram confirmation
```

## Error Handling

The application should handle errors without terminating the Telegram bot.

Possible errors include:

* Missing Gemini API key
* Invalid Telegram bot token
* Unsupported image format
* Unreadable receipt
* Missing receipt total
* Invalid AI response
* Gemini API failure
* Excel file permission error
* Spreadsheet file not found
* Network failure

Example user-facing error:

```text
I could not understand that expense. Please include the amount, currency, and description.
```

Example receipt error:

```text
I could not read the receipt clearly. Please upload a clearer image showing the merchant, date, and total amount.
```

Detailed technical errors should be written to application logs instead of being shown to the user.

## Logging

The application uses Python logging to track important events and errors.

Example log output:

```text
2026-06-07 21:24:57,210 | INFO | Processing manual expense
2026-06-07 21:24:57,213 | ERROR | Manual expense analysis failed
```

Recommended log levels:

* `DEBUG`: Detailed development information
* `INFO`: Normal application activity
* `WARNING`: Recoverable problems
* `ERROR`: Failed operations
* `CRITICAL`: Application-level failure

Never log API keys, Telegram tokens, or sensitive financial information.

## Testing

Run the test suite with:

```bash
uv run pytest
```

Suggested test coverage:

```text
tests/
├── test_command_handler.py
├── test_manual_expense_handler.py
├── test_receipt_parser.py
├── test_expense_models.py
└── test_expense_storage.py
```

Important test cases include:

* Valid manual expense
* Manual expense without an amount
* Manual expense without a currency
* Valid receipt image
* Blurry receipt image
* Receipt without a visible total
* Duplicate expense submission
* Invalid Gemini response
* Gemini API failure
* Excel write failure

## Development

Format the code:

```bash
uv run ruff format .
```

Check the code:

```bash
uv run ruff check .
```

Run type checking:

```bash
uv run mypy .
```

Run all tests:

```bash
uv run pytest
```

## Security

* Keep API keys inside environment variables.
* Never commit `.env` files.
* Validate every AI-generated response.
* Do not trust values extracted from receipt images without validation.
* Restrict Telegram bot access when the bot is intended for personal use.
* Avoid logging full receipt images or sensitive transaction details.
* Back up the Excel file regularly.
* Use file locking or controlled writes to avoid spreadsheet corruption.

## Limitations

* Receipt accuracy depends on image quality.
* Handwritten receipts may not be parsed correctly.
* Merchant names and categories may require manual correction.
* The same receipt could be recorded more than once unless duplicate detection is implemented.
* Excel storage is suitable for a personal project but may not scale well for multiple users.
* Currency conversion is not performed unless an exchange-rate service is added.

## Future Improvements

* Add duplicate receipt detection
* Add monthly spending summaries
* Add category-based budget limits
* Add spending charts and reports
* Add receipt correction commands
* Add expense editing and deletion
* Add CSV and PDF exports
* Add support for multiple users
* Replace Excel storage with a database
* Add recurring expense detection
* Add currency conversion
* Add Telegram inline buttons for confirmation
* Add automatic backup support
* Add dashboard integration

## Git Commit Example

```bash
git add .
```

```bash
git commit -m "feat: add AI-powered receipt parsing and expense extraction" \
  -m "Implement receipt image processing to extract merchant, date, total amount, currency, category, and purchased items. Integrate parsed receipt data with the expense tracking workflow, add validation and error handling, and store validated records in the financial usage spreadsheet."
```

## License

This project is currently intended for personal and educational use.

Add a license file before distributing or publishing the project publicly.

