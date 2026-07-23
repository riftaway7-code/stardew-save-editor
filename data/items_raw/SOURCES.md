# Item data sources

## stardewids_objects.json

- **Source**: https://github.com/MateusAquino/stardewids
- **File**: `dist/objects.json`, fetched from
  `https://raw.githubusercontent.com/MateusAquino/stardewids/main/dist/objects.json`
  on 2026-07-11.
- **License**: check the upstream repo for current terms before redistributing
  beyond personal/local use; this project uses it only as a local build input
  (not bundled/redistributed as source, only the compiled `data/items.json`
  ships with the app).
- **Contents**: 807 entries covering Stardew Valley 1.6's `Data/Objects` -
  crops, fish, forage, artisan goods, minerals, cooking ingredients, etc.
  Fields used: `id` (matches the save file's `<itemId>`/`<parentSheetIndex>`),
  `names['data-en-US']` (display name), `objectType` (rough category string).
- **Cross-checked**: spot-checked 6 IDs (Eggplant=272, Tilapia=701,
  Walleye=140, Parsnip=24, Large Goat Milk=438, Rainbow Shell=394) against
  independent Stardew Valley Wiki / stardewids.com lookups done manually -
  all 6 IDs matched (one abbreviated display name, "L. Goat Milk" vs "Large
  Goat Milk", same item).
- **Missing fields**: no numeric `category`/`price`/`edibility` (the fields
  the save's `<Item xsi:type="Object">` schema stores for those attributes).
  Per live device testing tonight, these fields are cosmetic-only in the
  save - the game recomputes real display/sell values from its own
  `Data/Objects` by `itemId` at load time regardless of what's stored, so
  `build_item_db.py` defaults them to safe placeholder values
  (`category=0`, `price=0`, `edibility=-300`) rather than guessing real
  ones from memory - never do that again after tonight's incident.
- **Sprites**: each entry also embeds a base64-encoded 16x16 PNG icon
  (`image` field) - this is the actual game sprite, verified visually
  (Parsnip #24 renders as a correct parsnip icon). `build_item_db.py`
  extracts these into `data/tilesheets/objects/<id>.png` for the map/item
  picker to render real pixel art instead of placeholder icons.

## stardewids_bigcraftables.json

- **Source**: same repo, `dist/big-craftables.json`, fetched
  2026-07-11. Covers placeable "big craftable" objects (Chest, furnaces,
  machines, etc.) - a separate data table from plain Objects in Stardew's
  own `Data/BigCraftables`. 182 entries. Same field shape and same
  sprite-extraction treatment, output to `data/tilesheets/bigcraftables/<id>.png`.
  Chest (#130) sprite visually verified.
