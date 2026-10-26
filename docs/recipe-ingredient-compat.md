# Pinned-pack recipe ingredient compatibility

Three server-data overrides repair missing ingredient references in the current
pack without hiding recipes, creating placeholder items, or changing client tags.
The root `kubejs/data` files and packaged server overrides must remain identical.

| Repair | Installed-resource evidence | Preserved behavior |
| --- | --- | --- |
| Magnolia item-tag alias | Regions Unexplored 0.5.6 ships `magnolia_logs_item` with four logs/woods, while the loaded EveryCompat hedge recipes request `magnolia_logs`. | Alias the existing item tag; do not redefine its members or replace other contributions. |
| Animal-fat dog food | Delightful 3.8.1 requests absent `farmersdelight:wolf_prey`; Farmer's Delight 1.3.4's own dog-food recipe uses `forge:raw_meat`. | Change only that ingredient reference; keep Delightful's `animal_fat` enable condition, quantities, output, cooking time, and experience. |
| Cheese cheesecake | Delightful's mild-or-sweet ingredient expands to a real flaxen cheese wedge plus an empty sweet-tag barrier in this pack. | Keep the mild tag and all currently accepted real cheese choices; keep the Collector's Reap exclusion and all other recipe fields. |

## Scope and verification

Cheesecake is deliberately scoped to this pinned pack: no installed sweet-cheese
provider supplies Delightful's optional `sob` or `farmlife` entries. Its condition
now requires a nonempty mild tag, matching the retained ingredient. Installing a
sweet-cheese provider later requires revisiting this override; it is not a generic
future-mod compatibility policy. The mild tag still permits its original optional
providers rather than hardcoding the currently installed flaxen cheese wedge.

Original mod resources are retained byte-for-byte in
`tests/fixtures/recipe-ingredient-compat`, with archive/resource SHA256 provenance
in `origins.json`. Tests compare complete recipe objects, allowing only the
documented edits, and assert root/package byte identity:

```powershell
python -B -m unittest discover -s tests -p test_recipe_ingredient_compat.py
```

Static contract checks do not prove runtime previews. A joint native lab join and
reconnect audit remains required after staging these overrides together with the
separate stale Create/JEI ingredient-cache fix. Public deployment and DH changes
are outside this unit. Rollback removes only these three mirrored data overrides.
