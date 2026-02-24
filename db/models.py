from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.engine import Base


class User(Base):
    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    full_name: Mapped[str] = mapped_column(String(256))
    role: Mapped[str] = mapped_column(String(64))
    city: Mapped[str] = mapped_column(String(128))
    organization: Mapped[str] = mapped_column(String(256))
    referral_source: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), default="new")  # new | applied | paid | onboarded
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    payment_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    onboarding_logs: Mapped[list["OnboardingLog"]] = relationship(back_populates="user")


class OnboardingLog(Base):
    __tablename__ = "onboarding_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.telegram_id"))
    message_key: Mapped[str] = mapped_column(String(64))
    # welcome | doc | invite | reminder_d1 | reminder_d3 | reminder_d7
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="onboarding_logs")


class CorporateRequest(Base):
    __tablename__ = "corporate_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger)
    theater_name: Mapped[str] = mapped_column(String(256))
    city: Mapped[str] = mapped_column(String(128))
    headcount: Mapped[int] = mapped_column(Integer)
    format: Mapped[str] = mapped_column(String(32))  # online | offline
    tasks_text: Mapped[str] = mapped_column(String(2000))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
