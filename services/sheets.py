import asyncio
import logging

import gspread
from google.oauth2.service_account import Credentials

from config import settings
from db.models import User
from texts.ru import REFERRAL_LABELS, ROLE_LABELS

log = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SHEET_HEADERS = [
    "telegram_id", "username", "full_name", "role",
    "city", "organization", "referral_source",
    "status", "applied_at", "paid_at", "payment_id",
]


def _get_worksheet():
    creds = Credentials.from_service_account_info(
        settings.google_credentials_dict,
        scopes=SCOPES,
    )
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(settings.google_sheet_id)
    return spreadsheet.sheet1


def _fmt_dt(dt) -> str:
    if dt is None:
        return ""
    return dt.strftime("%d.%m.%Y %H:%M")


def _write_row(user: User) -> None:
    ws = _get_worksheet()
    # Ensure headers exist
    existing = ws.row_values(1)
    if existing != SHEET_HEADERS:
        ws.insert_row(SHEET_HEADERS, index=1)

    row = [
        str(user.telegram_id),
        user.username or "",
        user.full_name,
        ROLE_LABELS.get(user.role, user.role),
        user.city,
        user.organization,
        REFERRAL_LABELS.get(user.referral_source, user.referral_source),
        user.status,
        _fmt_dt(user.applied_at),
        _fmt_dt(user.paid_at),
        user.payment_id or "",
    ]
    ws.append_row(row, value_input_option="USER_ENTERED")


async def append_application_row(user: User) -> None:
    """Синхронный gspread запускается в отдельном потоке."""
    await asyncio.to_thread(_write_row, user)
