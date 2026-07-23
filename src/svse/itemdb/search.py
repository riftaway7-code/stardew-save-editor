from __future__ import annotations

from svse.itemdb.loader import ItemDB
from svse.itemdb.models import Item


def search(db: ItemDB, query: str, limit: int = 50) -> list[Item]:
    """Simple case-insensitive substring search over item names, names
    starting with the query ranked first. Good enough for a GUI picker's
    search-as-you-type box; not doing fuzzy matching to keep results
    predictable (an exact-ish name match should never lose to a fuzzy one)."""
    query = query.strip().lower()
    if not query:
        return db.all()[:limit]

    starts_with: list[Item] = []
    contains: list[Item] = []
    for item in db.all():
        name_lower = item.name.lower()
        if name_lower.startswith(query):
            starts_with.append(item)
        elif query in name_lower:
            contains.append(item)

    starts_with.sort(key=lambda i: i.name)
    contains.sort(key=lambda i: i.name)
    return (starts_with + contains)[:limit]
