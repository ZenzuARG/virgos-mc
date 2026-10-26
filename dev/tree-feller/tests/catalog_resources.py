"""Reproduce the bounded installed-pack catalog from exact local JAR resources; no network."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import zipfile

PATTERNS = ("RegionsUnexplored*", "aether-*", "deep_aether-*", "alexscaves-*", "ars_nouveau-*", "twilightforest-*", "Quark-*")
ALIASES = {
    "alpha": "AlphaOakGrower", "ashen": "AshenPineGrower", "bamboo": "GiantBambooGrower",
    "brimwood": "BrimwoodGrower", "mauve": "MauveOakGrower", "pewen": "PewenGrower",
    "thornwood": "ThornwoodGrower", "darkwood": "DarkCanopyTreeGrower", "hollow_oak": "HollowTreeGrower",
    "rainbow_oak": "RainboakTreeGrower", "twilight_oak": "SmallOakTreeGrower",
}
TAG_ALIASES = {"brimwood": "brimwood_logs", "cobalt": "cobalt_logs",
    "blue_archwood": "cascading_logs", "green_archwood": "flourishing_logs",
    "purple_archwood": "vexing_logs", "red_archwood": "blazing_logs", "pewen": "pewen_logs", "thornwood": "thornwood_logs", "twilight_oak": "twilight_oak_logs",
    "hollow_oak": "twilight_oak_logs", "rainbow_oak": "twilight_oak_logs", "darkwood": "darkwood_logs",
    "time": "timewood_logs", "transformation": "transwood_logs", "sorting": "sortwood_logs", "mining": "mining_logs"}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for child in value:
            yield from strings(child)
    elif isinstance(value, dict):
        for child in value.values():
            yield from strings(child)


def class_metadata(data):
    pool = [None]
    offset = 10
    count = int.from_bytes(data[8:10], "big")
    while len(pool) < count:
        tag = data[offset]
        offset += 1
        if tag == 1:
            length = int.from_bytes(data[offset:offset + 2], "big")
            offset += 2
            pool.append(data[offset:offset + length].decode())
            offset += length
        elif tag == 7:
            pool.append(int.from_bytes(data[offset:offset + 2], "big"))
            offset += 2
        elif tag in (5, 6):
            pool.extend([None, None])
            offset += 8
        else:
            pool.append(None)
            offset += {3:4, 4:4, 8:2, 9:4, 10:4, 11:4, 12:4, 15:3, 16:2, 17:4, 18:4, 19:2, 20:2}[tag]
    superclass = pool[pool[int.from_bytes(data[offset + 4:offset + 6], "big")]]
    cursor = offset + 6
    cursor += 2 + 2 * int.from_bytes(data[cursor:cursor + 2], "big")
    # Skip fields, then inspect only method Code attributes (no class execution).
    def members(cursor, capture):
        count = int.from_bytes(data[cursor:cursor + 2], "big")
        cursor += 2
        result = []
        for _ in range(count):
            name = pool[int.from_bytes(data[cursor + 2:cursor + 4], "big")]
            descriptor = pool[int.from_bytes(data[cursor + 4:cursor + 6], "big")]
            attributes = int.from_bytes(data[cursor + 6:cursor + 8], "big")
            cursor += 8
            code = b""
            for _ in range(attributes):
                attribute = pool[int.from_bytes(data[cursor:cursor + 2], "big")]
                length = int.from_bytes(data[cursor + 2:cursor + 6], "big")
                cursor += 6
                if capture and attribute == "Code":
                    size = int.from_bytes(data[cursor + 4:cursor + 8], "big")
                    code = data[cursor + 8:cursor + 8 + size]
                cursor += length
            result.append((name, descriptor, code))
        return cursor, result
    cursor, _ = members(cursor, False)
    _, methods = members(cursor, True)
    return superclass, [item for item in pool if isinstance(item, str)], methods


def curate(mods):
    zeta_path = mods / "Zeta-1.0-31.jar"
    zeta_sha = "cd1786902a79434f8fd762d741019d9c8a79725fef7e30a89c153c934e1e6a9e"
    if sha(zeta_path.read_bytes()) != zeta_sha:
        raise ValueError("Pinned cross-JAR Zeta provider changed")
    with zipfile.ZipFile(zeta_path) as archive:
        if archive.testzip():
            raise ValueError("Bad Zeta CRC")
        zeta = {name: archive.read(name) for name in (
            "org/violetmoon/zeta/world/PassthroughTreeGrower.class", "org/violetmoon/zeta/block/ZetaSaplingBlock.class")}
    sources = [{"jar": zeta_path.name, "sha256": zeta_sha}]
    entries = []
    for pattern in PATTERNS:
        matches = list(mods.glob(pattern))
        if len(matches) != 1:
            raise ValueError("Expected one exact source for " + pattern)
        path = matches[0]
        with zipfile.ZipFile(path) as archive:
            if archive.testzip():
                raise ValueError("Bad source CRC")
            content = {name: archive.read(name) for name in archive.namelist() if not name.endswith("/")}
        sources.append({"jar": path.name, "sha256": sha(path.read_bytes())})
        blocks = {name.split("/")[1] + ":" + name.rsplit("/", 1)[1][:-5]: name for name in content
                  if name.startswith("assets/") and "/blockstates/" in name and name.endswith(".json")}
        seeds = sorted(key for key in blocks if key.endswith("_sapling") and not key.split(":")[1].startswith("potted_"))
        jsons = {name: json.loads(body) for name, body in content.items()
                 if name.startswith("data/") and name.endswith(".json") and any(part in name for part in ("/loot_tables/blocks/", "/worldgen/configured_feature/", "/tags/blocks/"))}
        def evidence(name):
            return {"path": name, "sha256": sha(content[name])}
        for seed in seeds:
            namespace, stem = seed.split(":")
            stem = stem.removesuffix("_sapling")
            refs = [evidence(blocks[seed])]
            leaves = set()
            for name, value in jsons.items():
                if "/loot_tables/blocks/" not in name or seed not in set(strings(value)):
                    continue
                block = namespace + ":" + name.rsplit("/", 1)[1][:-5]
                if block in blocks and block != seed and not block.split(":")[1].startswith("potted_"):
                    leaves.add(block)
                    refs.append(evidence(name))
            required_foliage = set(leaves)
            logs = set()
            for name, value in jsons.items():
                if "/worldgen/configured_feature/" not in name:
                    continue
                values = set(strings(value))
                if not values.intersection(leaves):
                    continue
                found = {item for item in values if item.endswith(("_log", "_wood", "_stem"))
                         and (item in blocks or item.startswith("minecraft:")) and "stripped_" not in item}
                if found:
                    logs.update(found)
                    leaves.update(item for item in values if (item in blocks or item.startswith("minecraft:")) and item.endswith("_leaves"))
                    refs.append(evidence(name))
            # Explicit resource-backed family distinctions where natural leaf loot is absent or shared.
            explicit_foliage = {"hollow_oak": "twilight_oak_leaves", "mining": "mining_leaves",
                "sorting": "sorting_leaves", "time": "time_leaves", "transformation": "transformation_leaves"}
            if namespace == "twilightforest" and stem in explicit_foliage:
                leaf = namespace + ":" + explicit_foliage[stem]
                if leaf not in blocks:
                    raise ValueError("Curated foliage disappeared")
                leaves.add(leaf)
                required_foliage.add(leaf)
                refs.append(evidence(blocks[leaf]))
            if namespace == "alexscaves" and stem == "pewen":
                # These exact blocks occur in the mod's minecraft:logs resource, not an inferred enum name.
                resource = "data/minecraft/tags/blocks/logs.json"
                declared = set(strings(jsons[resource]))
                for key in ("alexscaves:pewen_log", "alexscaves:pewen_wood"):
                    if key not in blocks or key not in declared:
                        raise ValueError("Curated pewen trunk disappeared")
                    logs.add(key)
                refs.append(evidence(resource))
            tag = TAG_ALIASES.get(stem)
            tag_path = "data/" + namespace + "/tags/blocks/" + str(tag) + ".json"
            if not logs and tag and tag_path in jsons:
                logs.update(item for item in strings(jsons[tag_path]) if item in blocks and "stripped_" not in item)
                refs.append(evidence(tag_path))
            # Explicit aliases plus exact existing class names; these are catalog evidence, never runtime suffix inference.
            title = "".join(part.title() for part in stem.split("_"))
            wanted = {ALIASES.get(stem, title + "TreeGrower")}
            if namespace == "aether":
                wanted = {title + "Tree"}
            grower = [(name, class_metadata(body)) for name, body in content.items()
                      if name.endswith(".class") and name.rsplit("/", 1)[1][:-6] in wanted]
            widths = []
            growth = "unresolved grower association"
            if len(grower) == 1:
                name, (parent, constants, methods) = grower[0]
                refs.append(evidence(name))
                # An override with a world/position boolean signature requires behavioral inspection, not name inference.
                overrides = any(value.startswith("(") and "ServerLevel;" in value and "BlockPos;" in value and value.endswith(")Z") for value in constants)
                if parent == "net/minecraft/world/level/block/grower/AbstractTreeGrower" and not overrides:
                    widths = [1]
                    growth = "inherits vanilla single-sapling grow path; root-shape/native acceptance pending"
                elif parent == "net/minecraft/world/level/block/grower/AbstractMegaTreeGrower" and not overrides:
                    # Do not assume that a subclass has a viable single-sapling alternative.
                    widths = [2]
                    normal = [code for _, descriptor, code in methods if descriptor.endswith(")Lnet/minecraft/resources/ResourceKey;") and ";Z)" in descriptor]
                    if len(normal) == 1 and len(normal[0]) == 4 and normal[0][0] == 178 and normal[0][-1] == 176:
                        widths.insert(0, 1)  # Exact GETSTATIC key; ARETURN, not a guessed nullable single path.
                    growth = "inherits vanilla mega path; single enabled only for verified GETSTATIC/ARETURN key; native/root acceptance pending"
                else:
                    growth = "custom/ultra/overridden grow path requires inspection: " + parent
            # Separate source seed requirements from the mature wood footprint. No inferred planting anchor.
            mature_widths = list(widths)
            planting_widths = list(widths)
            anchor_mode = "ROOT_GRID"
            if namespace == "ars_nouveau":
                colors = {"blue_archwood": "cascading_tree", "red_archwood": "blazing_tree",
                          "green_archwood": "flourishing_tree", "purple_archwood": "vexing_tree"}
                if stem not in colors:
                    raise ValueError("Unexpected archwood family")
                base = "com/hollingsworth/arsnouveau/common/"
                magic = base + "world/tree/MagicTree.class"
                parent, constants, methods = class_metadata(content[magic])
                if parent != "net/minecraft/world/level/block/grower/AbstractTreeGrower" or len(methods) != 2:
                    raise ValueError("MagicTree single-sapling route changed")
                feature = "data/ars_nouveau/worldgen/configured_feature/" + colors[stem] + ".json"
                natural = "data/ars_nouveau/worldgen/configured_feature/natural_" + colors[stem] + ".json"
                for resource in (feature, natural):
                    config = jsons[resource]["config"]
                    if config["trunk_placer"]["type"] != "ars_nouveau:magic_trunk_placer":
                        raise ValueError("Unexpected Ars trunk provider")
                    if namespace + ":" + config["trunk_provider"]["key"] not in logs or namespace + ":" + config["foliage_provider"]["key"] not in leaves:
                        raise ValueError("Archwood registry identity changed")
                    refs.append(evidence(resource))
                refs.extend(evidence(name) for name in (magic, "com/hollingsworth/arsnouveau/setup/registry/BlockRegistry.class",
                    base + "world/tree/MagicTrunkPlacer.class", base + "world/tree/SupplierBlockStateProvider.class"))
                mature_widths, planting_widths = [2], [1]
                anchor_mode = "UNRESOLVED_ARS_BUTTRESS"
                growth = "MagicTree single sapling; MagicTrunkPlacer.m_213934_ offsets230-289 2x2core,290-550 buttress roots; minimum1 is not mature4"
            if namespace == "quark":
                grower_name = "org/violetmoon/zeta/world/PassthroughTreeGrower.class"
                block_name = "org/violetmoon/zeta/block/ZetaSaplingBlock.class"
                parent, constants, methods = class_metadata(zeta[grower_name])
                block_parent, _, _ = class_metadata(zeta[block_name])
                if parent != "net/minecraft/world/level/block/grower/AbstractTreeGrower" or len(methods) != 2 or block_parent != "net/minecraft/world/level/block/SaplingBlock":
                    raise ValueError("Zeta single-sapling provider changed")
                module = "org/violetmoon/quark/content/world/module/" + ("AncientWoodModule.class" if stem == "ancient" else "BlossomTreesModule.class")
                _, constants, _ = class_metadata(content[module])
                if "org/violetmoon/zeta/world/PassthroughTreeGrower" not in constants or "org/violetmoon/zeta/block/ZetaSaplingBlock" not in constants:
                    raise ValueError("Quark constructor association changed")
                refs.append(evidence(module))
                refs.extend({"jar": zeta_path.name, "path": name, "sha256": sha(body)} for name, body in zeta.items())
                if stem == "ancient":
                    refs.append(evidence("org/violetmoon/quark/content/world/feature/MultiFoliageStraightTrunkPlacer.class"))
                mature_widths, planting_widths = [1], [1]
                growth = "Quark module constructs ZetaSaplingBlock(PassthroughTreeGrower(key)); inherited single-sapling path; mature fancy/vertical base1; native acceptance pending"
            widths = mature_widths
            gaps = []
            if not leaves:
                gaps.append("foliage mapping")
            if not logs:
                gaps.append("trunk mapping")
            if not mature_widths or not planting_widths:
                gaps.append("growth footprint")
            if anchor_mode == "UNRESOLVED_ARS_BUTTRESS":
                gaps.append("one-seed anchor within mature core/buttresses requires faithful geometry proof")
            if namespace == "twilightforest" and stem == "hollow_oak":
                gaps.append("shared oak identity requires verified hollow-root morphology")
            entries.append({"id": seed, "trunks": sorted(logs), "foliage": sorted(leaves), "required_foliage": sorted(required_foliage), "seeds": [seed],
                "fallback": seed, "widths": mature_widths, "mature_widths": mature_widths, "planting_widths": planting_widths,
                "anchor_mode": anchor_mode, "status": "READY_STATIC" if not gaps else "GAP: " + ", ".join(gaps),
                "growth_evidence": growth, "runtime": "UNPROVEN", "origin_jar": path.name, "evidence": sorted(refs, key=lambda item:item["path"])})
    if len(entries) != 64 or len({item["id"] for item in entries}) != 64:
        raise ValueError("Installed catalog inventory changed; review scope before regenerating")
    return {"schema": 2, "sources": sources, "inventory_count": 64,
            "scope_note": "Non-potted *_sapling variants only; not exhaustive vegetation, not native acceptance", "families": entries}


def write(catalog, output):
    output.mkdir(parents=True, exist_ok=True)
    (output / "catalog.json").write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")
    rows = []
    for family in catalog["families"]:
        rows.append("\t".join([family["id"], ",".join(family["trunks"]), ",".join(family["foliage"]),
            ",".join(family["seeds"]), family["fallback"], ",".join(map(str, family["widths"])), family["status"], ",".join(family["required_foliage"]), ",".join(map(str, family["planting_widths"])), family["anchor_mode"]]))
    (output / "catalog.tsv").write_text("\n".join(rows) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mods-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = curate(args.mods_root)
    write(result, args.output)
    print(json.dumps({"inventory": len(result["families"]), "static_ready": sum(item["status"] == "READY_STATIC" for item in result["families"]),
        "gaps": {item["id"]:item["status"] for item in result["families"] if item["status"] != "READY_STATIC"}}, indent=2))
