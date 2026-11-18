from sqlalchemy import and_, exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Material, MaterialGroup, MaterialLinkAccess, SharingGroupMember, User


def audience_condition(user: User):
    """One policy for notes, files, quizzes, imports and discovery."""
    group_access = exists(
        select(MaterialGroup.material_id)
        .join(SharingGroupMember, SharingGroupMember.group_id == MaterialGroup.group_id)
        .where(
            MaterialGroup.material_id == Material.id, SharingGroupMember.email == user.email.lower()
        )
    )
    link_access = exists(
        select(MaterialLinkAccess.material_id).where(
            MaterialLinkAccess.material_id == Material.id,
            MaterialLinkAccess.user_id == user.id,
            MaterialLinkAccess.token == Material.share_token,
        )
    )
    return or_(
        Material.user_id == user.id,
        Material.visibility == "public",
        and_(Material.is_public.is_(True), Material.visibility == "groups", group_access),
        and_(Material.is_public.is_(True), Material.visibility == "link", link_access),
    )


async def can_access(material: Material, user: User, session: AsyncSession) -> bool:
    return bool(
        await session.scalar(
            select(func.count())
            .select_from(Material)
            .where(Material.id == material.id, audience_condition(user))
        )
    )
