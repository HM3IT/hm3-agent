from datetime import date, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

from config import CHART_DIR, TZ

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

if TYPE_CHECKING:
    from services.excel_formatter import ExcelLedger


class ChartService:
    def __init__(self, ledger: "ExcelLedger") -> None:
        self.ledger = ledger

    @staticmethod
    def _normalize_date(value) -> date:
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        return date.fromisoformat(str(value))

    @staticmethod
    def _week_of_month(day: date) -> int:
        return ((day.day - 1) // 7) + 1

    def _all_rows(self) -> list[dict]:
        rows = self.ledger.load_expenses()
        clean_rows = []
        for row in rows:
            row_date = self._normalize_date(row["Transaction Date"])
            row_amount = float(row["Amount"])
            row_category = str(row["Category"])
            clean_rows.append(
                {
                    "date": row_date,
                    "amount": row_amount,
                    "category": row_category,
                }
            )
        return clean_rows

    def _category_totals(self, rows: list[dict]) -> dict[str, float]:
        totals: dict[str, float] = {}
        for row in rows:
            category = row["category"]
            totals[category] = totals.get(category, 0.0) + row["amount"]
        return totals

    @staticmethod
    def _autopct_with_amount(values):
        total = sum(values)

        def inner(pct):
            amount = total * pct / 100.0
            return f"{amount:,.0f} THB\n({pct:.1f}%)"

        return inner

    @staticmethod
    def _add_bar_labels(ax):
        for bar in ax.patches:
            height = bar.get_height()
            ax.annotate(
                f"{height:,.0f}",
                (bar.get_x() + bar.get_width() / 2, height),
                ha="center",
                va="bottom",
                xytext=(0, 5),
                textcoords="offset points",
                fontsize=10,
            )

    def weekly_bar_chart(self) -> tuple[Path, str] | None:
        today = datetime.now(TZ).date()
        start = today - timedelta(days=today.weekday())
        end = start + timedelta(days=6)

        rows = [row for row in self._all_rows() if start <= row["date"] <= end]
        if not rows:
            return None

        totals = self._category_totals(rows)
        categories = sorted(totals.keys())
        values = [totals[category] for category in categories]

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.bar(categories, values, label="This Week")
        ax.set_title(f"Weekly Spending by Category ({start} to {end})")
        ax.set_xlabel("Category")
        ax.set_ylabel("Amount (THB)")
        ax.tick_params(axis="x", rotation=35)
        ax.legend()
        self._add_bar_labels(ax)

        fig.tight_layout()
        path = CHART_DIR / f"weekly_bar_{start}.png"
        fig.savefig(path, dpi=160)
        plt.close(fig)
        return path, "Weekly bar chart"

    def weekly_pie_chart(self) -> tuple[Path, str] | None:
        today = datetime.now(TZ).date()
        start = today - timedelta(days=today.weekday())
        end = start + timedelta(days=6)

        rows = [row for row in self._all_rows() if start <= row["date"] <= end]
        if not rows:
            return None

        totals = self._category_totals(rows)
        categories = sorted(totals.keys())
        values = [totals[category] for category in categories]

        fig, ax = plt.subplots(figsize=(9, 8))
        wedges, _, _ = ax.pie(
            values,
            autopct=self._autopct_with_amount(values),
            startangle=90,
        )
        ax.set_title(f"Weekly Spending by Category ({start} to {end})")
        ax.legend(
            wedges,
            [f"{cat} — {val:,.0f} THB" for cat, val in zip(categories, values)],
            title="Categories",
            loc="center left",
            bbox_to_anchor=(1, 0.5),
        )
        fig.tight_layout()
        path = CHART_DIR / f"weekly_pie_{start}.png"
        fig.savefig(path, dpi=160, bbox_inches="tight")
        plt.close(fig)
        return path, "Weekly pie chart"

    def monthly_bar_chart(self) -> tuple[Path, str] | None:
        today = datetime.now(TZ).date()

        rows = [
            row
            for row in self._all_rows()
            if row["date"].year == today.year and row["date"].month == today.month
        ]
        if not rows:
            return None

        totals = self._category_totals(rows)
        categories = sorted(totals.keys())
        values = [totals[category] for category in categories]

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.bar(categories, values, label="This Month")
        ax.set_title(f"Monthly Spending by Category ({today:%Y-%m})")
        ax.set_xlabel("Category")
        ax.set_ylabel("Amount (THB)")
        ax.tick_params(axis="x", rotation=35)
        ax.legend()
        self._add_bar_labels(ax)

        fig.tight_layout()
        path = CHART_DIR / f"monthly_bar_{today:%Y_%m}.png"
        fig.savefig(path, dpi=160)
        plt.close(fig)
        return path, "Monthly bar chart"

    def monthly_pie_chart(self) -> tuple[Path, str] | None:
        today = datetime.now(TZ).date()

        rows = [
            row
            for row in self._all_rows()
            if row["date"].year == today.year and row["date"].month == today.month
        ]
        if not rows:
            return None

        totals = self._category_totals(rows)
        categories = sorted(totals.keys())
        values = [totals[category] for category in categories]

        fig, ax = plt.subplots(figsize=(9, 8))
        wedges, _, _ = ax.pie(
            values,
            autopct=self._autopct_with_amount(values),
            startangle=90,
        )
        ax.set_title(f"Monthly Spending by Category ({today:%Y-%m})")
        ax.legend(
            wedges,
            [f"{cat} — {val:,.0f} THB" for cat, val in zip(categories, values)],
            title="Categories",
            loc="center left",
            bbox_to_anchor=(1, 0.5),
        )
        fig.tight_layout()
        path = CHART_DIR / f"monthly_pie_{today:%Y_%m}.png"
        fig.savefig(path, dpi=160, bbox_inches="tight")
        plt.close(fig)
        return path, "Monthly pie chart"

    def month_vs_last_month_weekly_bar_chart(self) -> tuple[Path, str] | None:
        today = datetime.now(TZ).date()

        current_year = today.year
        current_month = today.month

        if current_month == 1:
            last_month = 12
            last_month_year = current_year - 1
        else:
            last_month = current_month - 1
            last_month_year = current_year

        rows = self._all_rows()

        current_rows = [
            row
            for row in rows
            if row["date"].year == current_year and row["date"].month == current_month
        ]
        last_rows = [
            row
            for row in rows
            if row["date"].year == last_month_year and row["date"].month == last_month
        ]

        if not current_rows and not last_rows:
            return None

        current_week_totals = {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0}
        last_week_totals = {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0}

        for row in current_rows:
            week_num = self._week_of_month(row["date"])
            if week_num in current_week_totals:
                current_week_totals[week_num] += row["amount"]

        for row in last_rows:
            week_num = self._week_of_month(row["date"])
            if week_num in last_week_totals:
                last_week_totals[week_num] += row["amount"]

        labels = [f"Week {i}" for i in range(1, 6)]
        current_values = [current_week_totals[i] for i in range(1, 6)]
        last_values = [last_week_totals[i] for i in range(1, 6)]

        x = list(range(len(labels)))
        width = 0.38

        fig, ax = plt.subplots(figsize=(11, 6))
        bars1 = ax.bar(
            [i - width / 2 for i in x],
            last_values,
            width,
            label=f"{last_month_year}-{last_month:02d}",
        )
        bars2 = ax.bar(
            [i + width / 2 for i in x],
            current_values,
            width,
            label=f"{current_year}-{current_month:02d}",
        )

        ax.set_title("This Month vs Last Month (Weekly Comparison)")
        ax.set_xlabel("Week of Month")
        ax.set_ylabel("Amount (THB)")
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.legend()

        self._add_bar_labels(ax)

        fig.tight_layout()
        path = CHART_DIR / f"month_vs_last_month_{today:%Y_%m}.png"
        fig.savefig(path, dpi=160)
        plt.close(fig)
        return path, "This month vs last month"
