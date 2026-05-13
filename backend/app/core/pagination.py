"""
Helper de paginación por cursor (keyset pagination).
Útil para list endpoints con grandes volúmenes de datos.
"""
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorCollection


async def paginate(
    collection: AsyncIOMotorCollection,
    filter: dict,
    sort_field: str = "created_at",
    limit: int = 50,
    cursor_value: Optional[str] = None,
    cursor_id: Optional[str] = None,
    extra_sort: Optional[list] = None,
) -> tuple[list[dict], Optional[dict]]:
    """
    Paginación por cursor (keyset) para colecciones MongoDB.
    
    Args:
        collection: Colección de MongoDB
        filter: Query filter
        sort_field: Campo para ordenar (default: created_at)
        limit: Items por página (default: 50, max: 200)
        cursor_value: Valor del cursor para la siguiente página
        cursor_id: ID del cursor para desambiguar
    
    Returns:
        (items, pagination_info) donde pagination_info tiene next_cursor si hay más
    """
    limit = min(limit, 200)
    query = dict(filter)

    # Keyset pagination
    if cursor_value and cursor_id:
        query["$or"] = [
            {sort_field: {"$lt": cursor_value}},
            {sort_field: cursor_value, "_id": {"$lt": cursor_id}},
        ]

    sort_criteria = [(sort_field, -1), ("_id", -1)]
    if extra_sort:
        sort_criteria = extra_sort + sort_criteria

    cursor = collection.find(query).sort(sort_criteria).limit(limit + 1)

    items = []
    async for doc in cursor:
        doc.pop("_id", None)
        items.append(doc)

    has_more = len(items) > limit
    if has_more:
        items = items[:limit]

    next_cursor = None
    if has_more and items:
        last = items[-1]
        next_cursor = {
            "value": str(last.get(sort_field, "")),
            "id": last.get("_id"),
        }

    return items, {"next_cursor": next_cursor, "has_more": has_more} if next_cursor else {"has_more": False}
