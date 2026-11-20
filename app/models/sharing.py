import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDPrimaryKeyMixin


class SharingGroup(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "sharing_groups"
    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(100))


class SharingGroupMember(Base):
    __tablename__ = "sharing_group_members"
    group_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sharing_groups.id", ondelete="CASCADE"), primary_key=True
    )
    email: Mapped[str] = mapped_column(String(320), primary_key=True)


class MaterialGroup(Base):
    __tablename__ = "material_groups"
    material_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("materials.id", ondelete="CASCADE"), primary_key=True
    )
    group_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sharing_groups.id", ondelete="CASCADE"), primary_key=True
    )


class MaterialLinkAccess(Base):
    __tablename__ = "material_link_access"
    material_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("materials.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    token: Mapped[str] = mapped_column(String(64))
