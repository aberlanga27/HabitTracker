from fastapi import APIRouter, status

from app.core.auth import ClockDep, CurrentUser, ViewerDep
from app.core.db import SessionDep
from app.schemas.errors import error_responses
from app.schemas.habits import HabitCreate, HabitList, HabitOrder, HabitRead, HabitUpdate
from app.services import habits as habit_service

router = APIRouter(prefix="/habits", tags=["habits"], responses=error_responses(401, 403))


def _to_list(items: list[HabitRead]) -> HabitList:
    return HabitList(items=items, total=len(items))


@router.get("")
def list_habits(session: SessionDep, viewer: ViewerDep, archived: bool = False) -> HabitList:
    return _to_list(habit_service.list_habits(session, viewer, archived=archived))


@router.post("", status_code=status.HTTP_201_CREATED, responses=error_responses(409, 422))
def create_habit(
    body: HabitCreate, session: SessionDep, clock: ClockDep, viewer: ViewerDep
) -> HabitRead:
    return habit_service.create(session, viewer, body, now=clock.now())


@router.put("/order", responses=error_responses(422))
def reorder_habits(body: HabitOrder, session: SessionDep, viewer: ViewerDep) -> HabitList:
    return _to_list(habit_service.reorder(session, viewer, body.habit_ids))


@router.get("/{habit_id}", responses=error_responses(404))
def get_habit(habit_id: str, session: SessionDep, viewer: ViewerDep) -> HabitRead:
    return habit_service.get(session, viewer, habit_id)


@router.patch("/{habit_id}", responses=error_responses(404, 422))
def update_habit(
    habit_id: str, body: HabitUpdate, session: SessionDep, viewer: ViewerDep
) -> HabitRead:
    return habit_service.update(session, viewer, habit_id, body)


@router.delete(
    "/{habit_id}", status_code=status.HTTP_204_NO_CONTENT, responses=error_responses(404)
)
def delete_habit(habit_id: str, user: CurrentUser, session: SessionDep) -> None:
    habit_service.delete(session, user.id, habit_id)


@router.post("/{habit_id}/archive", responses=error_responses(404))
def archive_habit(
    habit_id: str, session: SessionDep, clock: ClockDep, viewer: ViewerDep
) -> HabitRead:
    return habit_service.archive(session, viewer, habit_id, now=clock.now())


@router.post("/{habit_id}/restore", responses=error_responses(404, 409))
def restore_habit(habit_id: str, session: SessionDep, viewer: ViewerDep) -> HabitRead:
    return habit_service.restore(session, viewer, habit_id)
