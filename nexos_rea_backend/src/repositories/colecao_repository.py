import uuid

from sqlalchemy.orm import selectinload

from src.extensions.database import db
from src.models.models import Collection, CollectionItem


def find_by_id(collection_id: uuid.UUID) -> Collection | None:
    return db.session.get(Collection, collection_id)


def list_by_user(user_id: uuid.UUID) -> list[Collection]:
    result = db.session.execute(
        db.select(Collection)
        .where(Collection.user_id == user_id)
        .options(selectinload(Collection.items))
        .order_by(Collection.created_at.desc())
    )
    return list(result.scalars())


def create(user_id: uuid.UUID, title: str, visibility: str) -> Collection:
    col = Collection(user_id=user_id, title=title, visibility=visibility)
    db.session.add(col)
    db.session.commit()
    return col


def delete(collection: Collection) -> None:
    db.session.delete(collection)
    db.session.commit()


def find_item(collection_id: uuid.UUID, rea_id: uuid.UUID) -> CollectionItem | None:
    return db.session.get(CollectionItem, (collection_id, rea_id))


def add_item(collection_id: uuid.UUID, rea_id: uuid.UUID) -> CollectionItem:
    item = CollectionItem(collection_id=collection_id, rea_id=rea_id)
    db.session.add(item)
    db.session.commit()
    return item


def remove_item(item: CollectionItem) -> None:
    db.session.delete(item)
    db.session.commit()
