import hashlib

import mimetypes
import logging

from pathlib import Path
from typing import Optional

from db import StateStore
from services.excel_formatter import ExcelLedger
from services.chart_service import ChartService
from features.receipt_handler import ReceiptAnalyzer
from services.telegram_client import TelegramClient
 
from features.manual_expense_handler import ManualExpenseAnalyzer
 
from config import LOG_LEVEL, EXCEL_PATH, DOWNLOAD_DIR, ALLOWED_CHAT_ID
from datetime import datetime

from config import TZ
from schema import ReceiptData


logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("finance_bot")


def create_manual_receipt(
    expense,
    now: datetime,
) -> ReceiptData:
    return ReceiptData(
        merchant=expense.merchant or "Manual entry",
        transaction_date=now.date().isoformat(),
        transaction_time=now.strftime("%H:%M"),
        total_amount=expense.amount,
        currency="THB",
        category=expense.category,
        item_description=expense.description,
        payment_method=None,
        receipt_number=None,
        tax_amount=None,
        confidence=1.0,
        notes="Added manually from a Telegram text message.",
    )

def choose_upload(message: dict) -> Optional[dict]:
    if message.get("photo"):
        photo = message["photo"][-1]
        return {
            "file_id": photo["file_id"],
            "file_unique_id": photo["file_unique_id"],
            "filename": f"photo_{message['message_id']}.jpg",
            "mime_type": "image/jpeg",
        }

    document = message.get("document")
    if document:
        mime_type = (
            document.get("mime_type")
            or mimetypes.guess_type(document.get("file_name", ""))[0]
        )
        allowed = {
            "image/jpeg",
            "image/png",
            "image/webp",
            "application/pdf",
        }
        if mime_type not in allowed:
            return None
        return {
            "file_id": document["file_id"],
            "file_unique_id": document["file_unique_id"],
            "filename": document.get("file_name")
            or f"document_{message['message_id']}",
            "mime_type": mime_type,
        }
    return None


def make_source_key(chat_id: int, file_unique_id: str) -> str:
    raw = f"{chat_id}:{file_unique_id}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def make_manual_source_key(
    chat_id: int,
    message_id: int,
    item_index: int,
) -> str:
    raw = (
        f"manual:{chat_id}:{message_id}:{item_index}"
    ).encode("utf-8")

    return hashlib.sha256(raw).hexdigest()

def process_update(
    update: dict,
    *,
    telegram: TelegramClient,
    state: StateStore,
    analyzer: ReceiptAnalyzer,
    manual_analyzer: ManualExpenseAnalyzer,
    ledger: ExcelLedger,
    charts: ChartService,
) -> bool:
    message = update.get("message")
    if not message:
        return True

    chat_id = int(message["chat"]["id"])
    if not is_allowed(chat_id):
        logger.warning("Rejected message from unauthorized chat_id=%s", chat_id)
        return True

    command = command_name(message)

    if command:
        if process_command(
            command,
            chat_id,
            telegram,
            charts,
            state,
        ):
            return True

        telegram.send_message(
            chat_id,
            f"Unknown command: /{command}\n"
            "Use /help to see the available commands.",
        )
        return True

    text = (message.get("text") or "").strip()

    if state.is_manual_entry_pending(chat_id):
 
        if not text:
            telegram.send_message(
                chat_id,
                "Please send a text message describing the expense.",
            )
            return True

        try:
            result = manual_analyzer.analyze(text)
            now = datetime.now(TZ)
            saved_expenses = []

            for index, expense in enumerate(result.expenses):
                receipt = create_manual_receipt(expense, now)

                source_key = make_manual_source_key(
                    chat_id=chat_id,
                    message_id=int(message["message_id"]),
                    item_index=index,
                )

                inserted = ledger.append(
                    receipt,
                    source_key=source_key,
                    chat_id=chat_id,
                    message_id=int(message["message_id"]),
                    filename="manual-text-entry",
                )

                if inserted:
                    saved_expenses.append(receipt)

            state.clear_manual_entry(chat_id)

            if not saved_expenses:
                telegram.send_message(
                    chat_id,
                    "These expenses were already saved.",
                )
                return True

            lines = [
                f"Saved {len(saved_expenses)} expense(s):",
                "",
            ]

            total = 0.0

            for receipt in saved_expenses:
                lines.append(
                    f"• {receipt.category}: "
                    f"{receipt.total_amount:,.2f} THB — "
                    f"{receipt.item_description}"
                )
                total += receipt.total_amount

            lines.extend(
                [
                    "",
                    f"Total: {total:,.2f} THB",
                    f"Date: {now.date().isoformat()}",
                ]
            )

            telegram.send_message(
                chat_id,
                "\n".join(lines),
            )
            return True

        except Exception as exc:
            logger.exception("Manual expense analysis failed")

            telegram.send_message(
                chat_id,
                "I could not understand that expense.\n\n"
                "Please try again, for example:\n"
                "drink 50\n"
                "taxi 120 and coffee 50\n\n"
                "Use /cancel to stop.",
            )
            return True

    upload = choose_upload(message)

    if upload is None:
        telegram.send_message(
            chat_id,
            "Please send a receipt as a photo, JPG, PNG, WEBP, or PDF.",
        )
        return True

    source_key = make_source_key(chat_id, upload["file_unique_id"])
    if state.file_status(source_key) == "completed" or ledger.contains_source(
        source_key
    ):
        if state.file_status(source_key) != "completed":
            state.mark_completed(source_key)

        logger.info(
            "Skipping already processed receipt: source_key=%s",
            source_key,
        )
        return True

    safe_filename = Path(upload["filename"]).name
    local_path = DOWNLOAD_DIR / f"{source_key[:12]}_{safe_filename}"
    state.mark_started(
        source_key,
        upload["file_unique_id"],
        int(update["update_id"]),
        chat_id,
        int(message["message_id"]),
        safe_filename,
    )

    try:
        telegram.download_file(upload["file_id"], local_path)
        receipt = analyzer.analyze(local_path, upload["mime_type"])
        inserted = ledger.append(
            receipt,
            source_key=source_key,
            chat_id=chat_id,
            message_id=int(message["message_id"]),
            filename=safe_filename,
        )
        state.mark_completed(source_key)

        action = "Saved" if inserted else "Already saved"
        telegram.send_message(
            chat_id,
            f"{action}: {receipt.transaction_date}\n"
            f"{receipt.merchant}\n"
            f"{receipt.category}: {receipt.total_amount:,.2f} {receipt.currency}\n"
            f"{receipt.item_description}\n"
            f"Confidence: {receipt.confidence:.0%}",
        )
        return True
    except PermissionError:
        error_message = (
            f"Cannot save to {EXCEL_PATH}. "
            "The Excel file may currently be open. "
            "Please close financial_usage.xlsx. The receipt will be retried."
        )

        state.mark_failed(source_key, error_message)
        logger.exception("Excel file is locked")

        telegram.send_message(
            chat_id,
            "I read the receipt, but I could not save it because "
            "financial_usage.xlsx is open or locked.\n\n"
            "Please close the Excel file. I will retry the receipt.",
        )
        return False

    except Exception as exc:
        state.mark_failed(source_key, repr(exc))
        logger.exception("Receipt processing failed")

        telegram.send_message(
            chat_id,
            "I could not process this receipt. "
            f"It will be retried automatically.\n"
            f"Error: {type(exc).__name__}",
        )
        return False


def is_allowed(chat_id: int) -> bool:
    return not ALLOWED_CHAT_ID or str(chat_id) == ALLOWED_CHAT_ID


def command_name(message: dict) -> str:
    text = (message.get("text") or "").strip().lower()

    if not text.startswith("/"):
        return ""

    first = text.split()[0]
    return first[1:].split("@")[0]

def process_command(
    command: str,
    chat_id: int,
    telegram: TelegramClient,
    charts: ChartService,
    state: StateStore,
) -> bool:
    command_aliases = {
        "show_bar_chart": "show_week_bar_chart",
        "show_pie_chart": "show_month_pie_chart",
    }

    command = command_aliases.get(command, command)

    if command in {"start", "help"}:
        telegram.send_message(
            chat_id,
            "Send me a receipt image or PDF.\n\n"
            "Commands:\n"
            "/add_expense — add expenses without a receipt\n"
            "/cancel — cancel manual expense entry\n"
            "/show_week_bar_chart — weekly bar chart\n"
            "/show_week_pie_chart — weekly pie chart\n"
            "/show_month_bar_chart — monthly bar chart\n"
            "/show_month_pie_chart — monthly pie chart\n"
            "/show_month_compare_chart — this month vs last month\n"
            "/help — show this help",
        )
        return True

    if command == "add_expense":
        if state.is_manual_entry_pending(chat_id):
            telegram.send_message(
                chat_id,
                "Manual expense mode is already active.\n\n"
                "Send expenses such as:\n"
                "drink 50\n"
                "taxi 120 and coffee 50\n\n"
                "Use /cancel to stop.",
            )
            return True

        state.start_manual_entry(chat_id)

        telegram.send_message(
            chat_id,
            "Send one or more expenses in a normal message.\n\n"
            "Examples:\n"
            "drink 50\n"
            "taxi 120 and coffee 50\n"
            "lunch 80, water 20\n\n"
            "Use /cancel to stop.",
        )
        return True

    if command == "cancel":
        if state.is_manual_entry_pending(chat_id):
            state.clear_manual_entry(chat_id)

            telegram.send_message(
                chat_id,
                "Manual expense entry cancelled.",
            )
        else:
            telegram.send_message(
                chat_id,
                "There is no active manual expense entry.",
                )

        return True
    if command == "show_week_bar_chart":
        result = charts.weekly_bar_chart()
        if result is None:
            telegram.send_message(
                chat_id,
                "No spending data was found for this week.",
            )
            return True

        path, caption = result
        telegram.send_photo(chat_id, path, caption)
        return True

    if command == "show_week_pie_chart":
        result = charts.weekly_pie_chart()
        if result is None:
            telegram.send_message(
                chat_id,
                "No spending data was found for this week.",
            )
            return True

        path, caption = result
        telegram.send_photo(chat_id, path, caption)
        return True

    if command == "show_month_bar_chart":
        result = charts.monthly_bar_chart()
        if result is None:
            telegram.send_message(
                chat_id,
                "No spending data was found for this month.",
            )
            return True

        path, caption = result
        telegram.send_photo(chat_id, path, caption)
        return True

    if command == "show_month_pie_chart":
        result = charts.monthly_pie_chart()
        if result is None:
            telegram.send_message(
                chat_id,
                "No spending data was found for this month.",
            )
            return True

        path, caption = result
        telegram.send_photo(chat_id, path, caption)
        return True

    if command == "show_month_compare_chart":
        result = charts.month_vs_last_month_weekly_bar_chart()
        if result is None:
            telegram.send_message(
                chat_id,
                "No spending data was found for this month and last month.",
            )
            return True

        path, caption = result
        telegram.send_photo(chat_id, path, caption)
        return True

    return False