from datetime import date

from fastapi import APIRouter

from app.core.auth import ClockDep, CurrentUser
from app.core.db import SessionDep
from app.schemas.check_ins import CheckInList, CheckInSet, CheckInState
from app.schemas.errors import error_responses
from app.services import check_ins as check_in_service

router = APIRouter(tags=["check-ins"], responses=error_responses(401, 403))


@router.put("/habits/{habit_id}/check-ins/{date}", responses=error_responses(404, 409, 422))
def set_check_in(
    habit_id: str,
    date: date,
    body: CheckInSet,
    user: CurrentUser,
    session: SessionDep,
    clock: ClockDep,
) -> CheckInState:
    return check_in_service.set_check_in(session, user, habit_id, date, body, now=clock.now())


@router.get("/check-ins", responses=error_responses(422))
def list_check_ins(date: date, user: CurrentUser, session: SessionDep) -> CheckInList:
    items = list(check_in_service.list_for_date(session, user.id, date))
    return CheckInList(items=items, total=len(items))
