import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser
from app.db.session import get_session
from app.models import SharingGroup, SharingGroupMember
from app.schemas.public_material import SharingGroupRequest, SharingGroupResponse

router = APIRouter(prefix="/sharing-groups", tags=["sharing groups"])
Session = Annotated[AsyncSession, Depends(get_session)]


async def describe(group: SharingGroup, session: AsyncSession) -> SharingGroupResponse:
    emails = await session.scalars(
        select(SharingGroupMember.email)
        .where(SharingGroupMember.group_id == group.id)
        .order_by(SharingGroupMember.email)
    )
    return SharingGroupResponse(id=str(group.id), name=group.name, emails=list(emails))


async def owned(group_id: uuid.UUID, user_id: uuid.UUID, session: AsyncSession) -> SharingGroup:
    group = await session.scalar(
        select(SharingGroup)
        .where(SharingGroup.id == group_id, SharingGroup.owner_id == user_id)
        .with_for_update()
    )
    if group is None:
        raise HTTPException(404, "Group not found")
    return group


async def set_members(group: SharingGroup, body: SharingGroupRequest, session: AsyncSession):
    if not body.name.strip():
        raise HTTPException(422, "Invalid group name")
    group.name = body.name.strip()
    await session.execute(delete(SharingGroupMember).where(SharingGroupMember.group_id == group.id))
    session.add_all(
        [
            SharingGroupMember(group_id=group.id, email=email)
            for email in sorted({str(e).lower() for e in body.emails})
        ]
    )


@router.get("", response_model=list[SharingGroupResponse])
async def groups(current_user: CurrentUser, session: Session):
    rows = await session.scalars(
        select(SharingGroup)
        .where(SharingGroup.owner_id == current_user.id)
        .order_by(SharingGroup.name, SharingGroup.id)
    )
    return [await describe(group, session) for group in rows]


@router.post("", response_model=SharingGroupResponse, status_code=201)
async def create(body: SharingGroupRequest, current_user: CurrentUser, session: Session):
    group = SharingGroup(owner_id=current_user.id, name=body.name.strip())
    session.add(group)
    await session.flush()
    await set_members(group, body, session)
    await session.commit()
    return await describe(group, session)


@router.put("/{group_id}", response_model=SharingGroupResponse)
async def update(
    group_id: uuid.UUID, body: SharingGroupRequest, current_user: CurrentUser, session: Session
):
    group = await owned(group_id, current_user.id, session)
    await set_members(group, body, session)
    await session.commit()
    return await describe(group, session)


@router.delete("/{group_id}", status_code=204)
async def remove(group_id: uuid.UUID, current_user: CurrentUser, session: Session):
    group = await owned(group_id, current_user.id, session)
    await session.delete(group)
    await session.commit()
