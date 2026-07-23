#!/usr/bin/env python3
"""One-time offline build: data/items_raw/ -> data/items.json + sprite PNGs.

Not imported by the running app - nothing at runtime ever depends on the
network. Re-run this manually after updating a raw source; commit the
resulting data/items.json and data/tilesheets/.

See data/items_raw/SOURCES.md for provenance of every input file, including
why price/edibility/category are defaulted rather than sourced (verified
cosmetic-only in the save format, see project plan).

IMPORTANT: Data/Objects and Data/BigCraftables are separate ID namespaces in
Stardew's own data (a real save's <Item xsi:type="Object"> and a placed
<Object xsi:type="Chest">'s itemId both reference different tables that can
and do share numeric IDs - 134 collisions found between the two raw source
files used here). They are kept as two separate top-level dicts
(`items` / `bigcraftables`) in the compiled JSON and two separate sprite
directories - never merge them into one flat id-keyed dict.
"""

from __future__ import annotations

import base64
import json
from pathlib import Path

RAW_DIR = Path(__file__).parent.parent / "data" / "items_raw"
OUT_PATH = Path(__file__).parent.parent / "data" / "items.json"
TILESHEETS_DIR = Path(__file__).parent.parent / "data" / "tilesheets"

# Placeholders for fields the save schema wants but the game recomputes at
# runtime from its own Data/Objects by itemId regardless of what's stored -
# see SOURCES.md. Never guess "plausible" values here; these must stay
# obviously-inert placeholders, not fake real-looking data.
_DEFAULT_CATEGORY = 0
_DEFAULT_PRICE = 0
_DEFAULT_EDIBILITY = -300


def _build_table(raw_path: Path, sprite_subdir: str) -> tuple[dict, int, int]:
    with open(raw_path, encoding="utf-8") as f:
        raw_items = json.load(f)

    sprite_dir = TILESHEETS_DIR / sprite_subdir
    sprite_dir.mkdir(parents=True, exist_ok=True)

    items: dict[str, dict] = {}
    skipped = 0
    sprites_written = 0
    for entry in raw_items:
        item_id = entry.get("id")
        name = entry.get("names", {}).get("data-en-US")
        if not item_id or not name:
            skipped += 1
            continue
        if item_id in items:
            skipped += 1
            continue

        has_sprite = False
        image_b64 = entry.get("image")
        if image_b64:
            try:
                sprite_bytes = base64.b64decode(image_b64)
                (sprite_dir / f"{item_id}.png").write_bytes(sprite_bytes)
                has_sprite = True
                sprites_written += 1
            except Exception:
                pass  # missing sprite is non-fatal; renderer falls back to a placeholder

        items[item_id] = {
            "id": item_id,
            "name": name,
            "object_type": entry.get("objectType", "Basic"),
            "category": _DEFAULT_CATEGORY,
            "price": _DEFAULT_PRICE,
            "edibility": _DEFAULT_EDIBILITY,
            "has_sprite": has_sprite,
        }

    return items, skipped, sprites_written


def build() -> dict:
    objects, obj_skipped, obj_sprites = _build_table(RAW_DIR / "stardewids_objects.json", "objects")
    bigcraftables, bc_skipped, bc_sprites = _build_table(
        RAW_DIR / "stardewids_bigcraftables.json", "bigcraftables"
    )

    return {
        "schema_version": 2,
        "source": "data/items_raw/ (see SOURCES.md)",
        "count": len(objects),
        "skipped": obj_skipped,
        "bigcraftable_count": len(bigcraftables),
        "bigcraftable_skipped": bc_skipped,
        "sprites_written": obj_sprites + bc_sprites,
        "items": objects,
        "bigcraftables": bigcraftables,
    }


def main() -> None:
    result = build()
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, sort_keys=True, ensure_ascii=False)
        f.write("\n")

    by_type: dict[str, int] = {}
    for item in result["items"].values():
        by_type[item["object_type"]] = by_type.get(item["object_type"], 0) + 1

    print(f"Wrote {OUT_PATH}")
    print(f"  objects: {result['count']} ({result['skipped']} skipped)")
    print(f"  bigcraftables: {result['bigcraftable_count']} ({result['bigcraftable_skipped']} skipped)")
    print(f"  sprites written: {result['sprites_written']} -> {TILESHEETS_DIR}")
    print("  objects by object_type:")
    for object_type, count in sorted(by_type.items(), key=lambda kv: -kv[1]):
        print(f"    {object_type}: {count}")


if __name__ == "__main__":
    main()
