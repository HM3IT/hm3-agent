import time
import logging

from db import StateStore
from services.excel_formatter import ExcelLedger
from services.chart_service import ChartService
from features.receipt_handler import ReceiptAnalyzer
from services.telegram_client import TelegramClient
from features.command_handler import process_update
from features.manual_expense_handler import ManualExpenseAnalyzer
from config import (
    RETRY_SECONDS,
    LOG_LEVEL,
    DB_PATH,
    EXCEL_PATH
)

 
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("finance_bot")


def main() -> None:
    telegram = TelegramClient()
    state = StateStore(DB_PATH)
    analyzer = ReceiptAnalyzer()
    ledger = ExcelLedger(EXCEL_PATH)
    charts = ChartService(ledger)
    manual_analyzer = ManualExpenseAnalyzer()

    # getUpdates does not work while a webhook is active.
    # Keeping pending updates preserves the Telegram backlog.
    telegram.delete_webhook()
    telegram.delete_commands()
    telegram.set_commands()

    logger.info("Telegram commands registered.")
    logger.info("Bot started. Excel file: %s", EXCEL_PATH)
    while True:
        try:
            offset = state.get_next_offset()
            updates = telegram.get_updates(offset)

            for update in sorted(
                updates,
                key=lambda item: item["update_id"],
            ):
                success = process_update(
                    update,
                    telegram=telegram,
                    state=state,
                    analyzer=analyzer,
                    manual_analyzer=manual_analyzer,
                    ledger=ledger,
                    charts=charts,
                )

                if not success:
                    # Do not advance the offset.
                    # The failed update will be retried later.
                    logger.warning(
                        "Update %s failed. Retrying in %s seconds.",
                        update["update_id"],
                        RETRY_SECONDS,
                    )
                    time.sleep(RETRY_SECONDS)
                    break

                # Confirm that this update was handled successfully.
                state.set_next_offset(int(update["update_id"]) + 1)

        except KeyboardInterrupt:
            logger.info("Bot stopped by user.")
            break

        except Exception:
            logger.exception("Polling error")
            time.sleep(RETRY_SECONDS)


if __name__ == "__main__":
    main()
