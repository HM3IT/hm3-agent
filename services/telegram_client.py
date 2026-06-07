import json

from pathlib import Path
from typing import Optional

import requests
from config import TELEGRAM_API, TELEGRAM_FILE_API, POLL_TIMEOUT


class TelegramClient:
    def set_commands(self) -> None:
        commands = [
            {
                "command": "show_week_bar_chart",
                "description": "Weekly spending bar chart",
            },
            {
                "command": "show_week_pie_chart",
                "description": "Weekly spending pie chart",
            },
            {
                "command": "show_month_bar_chart",
                "description": "Monthly spending bar chart",
            },
            {
                "command": "show_month_pie_chart",
                "description": "Monthly spending pie chart",
            },
            {
                "command": "show_month_compare_chart",
                "description": "This month vs last month",
            },
            {
                "command": "add_expense",
                "description": "Add an expense without a receipt",
            },
            {
                "command": "cancel",
                "description": "Cancel manual expense entry",
            },
        ]

        self.call(
            "setMyCommands",
            params={
                "commands": json.dumps(commands),
            },
        )

    def delete_commands(self) -> None:
        self.call("deleteMyCommands")

    def call(self, method: str, *, params=None, files=None, timeout=60):
        response = requests.post(
            f"{TELEGRAM_API}/{method}",
            data=params,
            files=files,
            timeout=timeout,
        )
        response.raise_for_status()

        payload = response.json()

        if not payload.get("ok"):
            raise RuntimeError(f"Telegram API error: {payload}")

        return payload["result"]

    def delete_webhook(self) -> None:
        self.call("deleteWebhook", params={"drop_pending_updates": "false"})

    def get_updates(self, offset: Optional[int]) -> list[dict]:
        params = {
            "timeout": POLL_TIMEOUT,
            "limit": 100,
            "allowed_updates": json.dumps(["message"]),
        }
        if offset is not None:
            params["offset"] = offset
        return self.call(
            "getUpdates",
            params=params,
            timeout=POLL_TIMEOUT + 15,
        )

    def send_message(self, chat_id: int, text: str) -> None:
        self.call(
            "sendMessage",
            params={"chat_id": chat_id, "text": text},
        )

    def send_photo(self, chat_id: int, path: Path, caption: str) -> None:
        with path.open("rb") as file_handle:
            self.call(
                "sendPhoto",
                params={"chat_id": chat_id, "caption": caption},
                files={"photo": file_handle},
                timeout=120,
            )

    def get_file_path(self, file_id: str) -> str:
        result = self.call("getFile", params={"file_id": file_id})
        return result["file_path"]

    def download_file(self, file_id: str, destination: Path) -> None:
        remote_path = self.get_file_path(file_id)
        response = requests.get(
            f"{TELEGRAM_FILE_API}/{remote_path}",
            timeout=120,
        )
        response.raise_for_status()
        destination.write_bytes(response.content)
