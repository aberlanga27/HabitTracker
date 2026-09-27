from datetime import date

from fastapi import APIRouter

from app.core.auth import CurrentUser, TodayDep
from app.core.db import SessionDep
from app.schemas.days import DaySummary
from app.schemas.errors import error_responses
from app.services import days as day_service

router = APIRouter(prefix="/days", tags=["days"], responses=error_responses(401))


@router.get("/{date}", responses=error_responses(422))
def get_day(date: date, user: CurrentUser, session: SessionDep, today: TodayDep) -> DaySummary:
    return day_service.day_summary(session, user.id, date, today=today)
