#!/usr/bin/env python3
"""Build the pinned server-only overlay without downloads, credentials, or source-tree outputs."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def replace_once(text, before, after):
    if text.count(before) != 1:
        raise ValueError("Patch context must occur exactly once")
    return text.replace(before, after, 1)


def safe_entry(name):
    path = PurePosixPath(name)
    return bool(name) and not path.is_absolute() and ".." not in path.parts and ":" not in name and "\\" not in name


def allowed_class(name):
    declared = {
        "com/thizthizzydizzy/treefeller/TreeFeller.class",
        "com/thizthizzydizzy/treefeller/Sapling.class",
        "mc/virgos/forestry/Balance.class", "mc/virgos/forestry/Forestry.class",
        "mc/virgos/forestry/Forestry$Operation.class", "mc/virgos/forestry/Journal.class",
        "mc/virgos/forestry/Journal$Group.class", "mc/virgos/forestry/NativeGuard.class",
        "mc/virgos/forestry/Catalog.class", "mc/virgos/forestry/Catalog$Definition.class",
        "mc/virgos/forestry/MaterialBindings.class",
    }
    declared.update("com/thizthizzydizzy/treefeller/TreeFeller$" + str(index) + ".class" for index in range(1, 7))
    return name in declared


def checked(path, expected):
    path = Path(path).resolve(strict=True)
    if sha(path) != expected:
        raise ValueError("Pinned input hash mismatch: " + path.name)
    return path


def archive(path):
    with zipfile.ZipFile(path) as source:
        bad = source.testzip()
        if bad:
            raise ValueError("CRC mismatch: " + bad)
        result = {}
        for entry in source.infolist():
            if not safe_entry(entry.filename):
                raise ValueError("Unsafe ZIP path")
            if not entry.is_dir():
                if entry.filename in result:
                    raise ValueError("Duplicate ZIP entry")
                result[entry.filename] = source.read(entry)
        return result


def write_zip(path, contents):
    with zipfile.ZipFile(path, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as target:
        for name, body in sorted(contents.items()):
            if not safe_entry(name):
                raise ValueError("Unsafe output path")
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            target.writestr(info, body)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upstream-jar", required=True, type=Path, help="Verified official TreeFeller-1.33.0.jar")
    parser.add_argument("--source-zip", required=True, type=Path, help="Pinned complete upstream source archive")
    parser.add_argument("--bukkit-api", required=True, type=Path, help="Pinned Ketting universal jar containing Bukkit API")
    parser.add_argument("--coreprotect-api", required=True, type=Path, help="Strictly pinned official public CoreProtect-CE-24.1.jar compile-only API provider")
    parser.add_argument("--classpath", action="append", default=[], type=Path, help="Additional existing local API jar; repeatable, recorded in evidence")
    parser.add_argument("--jdk", required=True, type=Path, help="Local Java 17 JDK home")
    parser.add_argument("--output", required=True, type=Path, help="NEW output directory outside the repository")
    parser.add_argument("--compatibility-jar", type=Path, help="Optional pinned .2 diagnostic JAR for prior public journal/catalog differentials")
    parser.add_argument("--tests", action="store_true", help="Compile/run standalone journal, metadata/layout and durability public-interface probes")
    args = parser.parse_args()
    pin = json.loads((ROOT / "UPSTREAM.json").read_text())
    resources = {"META-INF/virgos-tree-feller/" + name: checked(ROOT / "resources" / name, digest).read_bytes()
                 for name, digest in pin["resources"].items()}
    if {path.name for path in (ROOT / "resources").iterdir() if path.is_file()} != set(pin["resources"]):
        raise ValueError("Undeclared runtime resources")
    upstream = checked(args.upstream_jar, pin["jar"]["sha256"])
    source_zip = checked(args.source_zip, pin["source"]["sha256"])
    bukkit = checked(args.bukkit_api, pin["compile_inputs"]["ketting_universal_sha256"])
    coreprotect = checked(args.coreprotect_api, pin["compile_inputs"]["coreprotect_sha256"])
    with zipfile.ZipFile(coreprotect) as provider:
        if provider.testzip():
            raise ValueError("CoreProtect provider CRC mismatch")
        for name, expected in pin["coreprotect_compile_provider"]["referenced_classes_sha256"].items():
            if hashlib.sha256(provider.read(name)).hexdigest() != expected:
                raise ValueError("CoreProtect referenced API class changed")
    compatibility = checked(args.compatibility_jar, pin["previous_candidate"]["jar_sha256"]) if args.compatibility_jar else None
    dependencies = []
    for path in args.classpath:
        expected = pin["compile_inputs"]["additional_jars"].get(path.name)
        if expected is None:
            raise ValueError("Undeclared additional API jar")
        dependencies.append(checked(path, expected))
    output = args.output.resolve()
    if output.is_relative_to(ROOT.parents[1]) or output.exists():
        raise ValueError("Output must be NEW and outside the repository")
    javac = args.jdk / "bin" / ("javac.exe" if os.name == "nt" else "javac")
    java = args.jdk / "bin" / ("java.exe" if os.name == "nt" else "java")
    version = subprocess.run([str(javac), "-J-Xmx256m", "-version"], capture_output=True, text=True, check=True)
    if not (version.stdout + version.stderr).startswith("javac 17."):
        raise ValueError("A Java 17 compiler is required")
    sources = archive(source_zip)
    roots = {name.split("/", 1)[0] for name in sources}
    if len(roots) != 1:
        raise ValueError("Expected one upstream source root")
    prefix = roots.pop() + "/"
    sources = {name[len(prefix):]: body for name, body in sources.items()}
    if sources["LICENSE"] != (ROOT / "LICENSE").read_bytes():
        raise ValueError("Upstream license changed")
    patches = []
    for patch_path in sorted((ROOT / "patches").glob("*.json")):
        patch = json.loads(patch_path.read_text())
        body = sources[patch["path"]]
        if hashlib.sha256(body).hexdigest() != patch["source_sha256"]:
            raise ValueError("Unexpected upstream source context")
        text = body.decode("utf-8").replace("\r\n", "\n")
        for replacement in patch["replacements"]:
            text = replace_once(text, replacement["before"], replacement["after"])
        sources[patch["path"]] = text.encode("utf-8")
        patches.append(patch["path"])
    output.mkdir(parents=True)
    work = output / "work"
    classes = work / "classes"
    classes.mkdir(parents=True)
    units = []
    for name in patches:
        target = work / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(sources[name])
        units.append(target)
    units += sorted((ROOT / "src/main/java").rglob("*.java"))
    cp = os.pathsep.join(str(path) for path in [upstream, bukkit, coreprotect] + dependencies)
    command = [str(javac), "-J-Xmx256m", "--release", "17", "-encoding", "UTF-8", "-proc:none", "-implicit:none", "-sourcepath", str(work / "empty"), "-cp", cp, "-d", str(classes)] + [str(path) for path in units]
    result = subprocess.run(command, text=True, capture_output=True)
    (output / "compile.stdout").write_text(result.stdout, encoding="utf-8")
    (output / "compile.stderr").write_text(result.stderr, encoding="utf-8")
    if result.returncode:
        raise RuntimeError("Compilation failed; see external compile.stderr")
    overlay = {path.relative_to(classes).as_posix(): path.read_bytes() for path in classes.rglob("*.class")}
    if not overlay or any(not allowed_class(name) for name in overlay):
        raise ValueError("Unexpected compiled class footprint")
    for name, body in resources.items():
        target = classes / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(body)
    contents = archive(upstream)
    # The original manifest's Main-Class is an upstream config generator, never executed here.
    # Remove signature metadata when modifying any signed upstream archive.
    if any(name.upper().endswith((".SF", ".RSA", ".DSA")) for name in contents):
        raise ValueError("Unexpected signed upstream archive; refusing overlay")
    expected_nested = {name for name in contents if name.startswith("com/thizthizzydizzy/treefeller/TreeFeller$") and name.endswith(".class")}
    actual_nested = {name for name in overlay if name.startswith("com/thizthizzydizzy/treefeller/TreeFeller$")}
    if expected_nested != actual_nested:
        raise ValueError("Unexpected upstream nested class footprint")
    contents.update(overlay)
    contents.update(resources)
    plugin = contents["plugin.yml"].decode("utf-8")
    plugin = replace_once(plugin, "version: 1.33.0", "version: " + pin["modified_version"])
    if "\ndepend:" in plugin:
        raise ValueError("Unexpected dependency declaration")
    plugin = replace_once(plugin, "  - CoreProtect\n", "")
    plugin += "\ndepend: [CoreProtect]\n"
    contents["plugin.yml"] = plugin.encode("utf-8")
    contents["META-INF/virgos-tree-feller/UPSTREAM.json"] = (ROOT / "UPSTREAM.json").read_bytes()
    contents["META-INF/virgos-tree-feller/LICENSE"] = (ROOT / "LICENSE").read_bytes()
    jar = output / ("TreeFeller-" + pin["modified_version"] + ".jar")
    write_zip(jar, contents)
    corresponding = {"upstream/" + name: body for name, body in sources.items()}
    for path in ROOT.rglob("*"):
        if path.is_file() and "__pycache__" not in path.parts:
            corresponding["virgos-fork/" + path.relative_to(ROOT).as_posix()] = path.read_bytes()
    full_source = output / ("TreeFeller-" + pin["modified_version"] + "-sources.zip")
    corresponding["pinned-inputs/source.zip"] = source_zip.read_bytes()
    corresponding["pinned-inputs/TreeFeller-1.33.0.jar"] = upstream.read_bytes()
    write_zip(full_source, corresponding)
    tests = []
    if args.tests:
        test_classes = work / "test-classes"
        test_classes.mkdir()
        test_sources = sorted((ROOT / "src/test/java").rglob("*.java"))
        subprocess.run([str(javac), "-J-Xmx256m", "--release", "17", "-cp", os.pathsep.join([str(classes), cp]), "-d", str(test_classes)] + [str(path) for path in test_sources], check=True)
        for name in ("JournalTest", "BalanceTest", "EngineConfigTest", "LegacySaplingTest", "PistonProvenanceTest", "DeclaredSpeciesTest", "AlternativeJournalTest", "LegacyJournalTest", "CatalogTest", "PlantingLayoutTest"):
            test_data = output / ("test-data-" + name)
            test_data.mkdir()
            (test_data / "upstream-config.yml").write_bytes(sources["src/config.yml"])
            run = subprocess.run([str(java), "-Xmx256m", "-cp", os.pathsep.join([str(classes), str(test_classes), cp]), "mc.virgos.forestry." + name, str(test_data)], text=True, capture_output=True)
            tests.append({"name": name, "exit": run.returncode, "stdout": run.stdout, "stderr": run.stderr})
        differential = []
        for kind, runtime_cp in (
            ("upstream", os.pathsep.join([str(upstream), str(test_classes), str(bukkit), str(coreprotect)] + [str(path) for path in dependencies])),
            ("candidate", os.pathsep.join([str(classes), str(test_classes), cp]))):
            probe = subprocess.run([str(java), "-Xmx256m", "-cp", runtime_cp, "mc.virgos.forestry.EngineDifferentialProbe"], text=True, capture_output=True)
            differential.append({"kind": kind, "exit": probe.returncode, "stdout": probe.stdout, "stderr": probe.stderr})
        (output / "differential.json").write_text(json.dumps(differential, indent=2) + "\n")
        same = all(differential[0][key] == differential[1][key] for key in ("exit", "stdout", "stderr")) and differential[0]["exit"] == 0
        tests.append({"name": "EngineDifferentialProbe", "exit": 0 if same else 1,
            "stdout": "upstream/candidate stdout, stderr and exit identical" if same else "differential mismatch", "stderr": ""})
        journal_diff = []
        if compatibility:
            for kind, runtime_cp in (
                ("previous", os.pathsep.join([str(compatibility), str(test_classes), cp])),
                ("candidate", os.pathsep.join([str(classes), str(test_classes), cp]))):
                directory = output / ("journal-differential-" + kind)
                directory.mkdir()
                probe = subprocess.run([str(java), "-Xmx256m", "-cp", runtime_cp, "mc.virgos.forestry.JournalDifferentialProbe", str(directory)], text=True, capture_output=True)
                journal_diff.append({"kind": kind, "exit": probe.returncode, "stdout": probe.stdout, "stderr": probe.stderr})
            (output / "journal-differential.json").write_text(json.dumps(journal_diff, indent=2) + "\n")
            same = all(journal_diff[0][key] == journal_diff[1][key] for key in ("exit", "stdout", "stderr")) and journal_diff[0]["exit"] == 0
            tests.append({"name": "JournalDifferentialProbe", "exit": 0 if same else 1,
                "stdout": "previous/candidate logical stdout, stderr, exit and rejected-byte invariants identical" if same else "journal differential mismatch", "stderr": ""})
        else:
            tests.append({"name": "JournalDifferentialProbe", "exit": 0, "status": "SKIPPED", "stdout": "--compatibility-jar not supplied", "stderr": ""})
        catalog_diff = []
        if compatibility:
            for kind, runtime_cp in (
                ("previous", os.pathsep.join([str(compatibility), str(test_classes), cp])),
                ("candidate", os.pathsep.join([str(classes), str(test_classes), cp]))):
                probe = subprocess.run([str(java), "-Xmx256m", "-cp", runtime_cp, "mc.virgos.forestry.CatalogCompatibilityProbe"], text=True, capture_output=True)
                catalog_diff.append({"kind": kind, "exit": probe.returncode, "stdout": probe.stdout, "stderr": probe.stderr})
            (output / "catalog-differential.json").write_text(json.dumps(catalog_diff, indent=2) + "\n")
            same = all(catalog_diff[0][key] == catalog_diff[1][key] for key in ("exit", "stdout", "stderr")) and catalog_diff[0]["exit"] == 0
            tests.append({"name": "CatalogCompatibilityProbe", "exit": 0 if same else 1,
                "stdout": "previous/candidate pre-.3 constructor, vanilla identities and old accessors identical" if same else "catalog differential mismatch", "stderr": ""})
        else:
            tests.append({"name": "CatalogCompatibilityProbe", "exit": 0, "status": "SKIPPED", "stdout": "--compatibility-jar not supplied", "stderr": ""})
        (output / "tests.json").write_text(json.dumps(tests, indent=2) + "\n")
        if any(test["exit"] for test in tests):
            raise RuntimeError("Standalone test failure; see tests.json")
    catalog = json.loads((ROOT / "resources/catalog.json").read_text())
    evidence = {"catalog": {"inventory": catalog["inventory_count"],
        "static_ready": sum(item["status"] == "READY_STATIC" for item in catalog["families"]),
        "gaps": {item["id"]: item["status"] for item in catalog["families"] if item["status"] != "READY_STATIC"},
        "runtime_binding_and_native_acceptance": "UNPROVEN"}, "upstream_commit": pin["commit"], "jar": {"path": str(jar), "sha256": sha(jar)},
        "corresponding_source": {"path": str(full_source), "sha256": sha(full_source)},
        "overlay_classes": sorted(overlay), "unmodified_engine_classes": len([name for name in contents if name.endswith(".class") and name not in overlay]),
        "compile_inputs": [{"name": path.name, "sha256": sha(path)} for path in [upstream, bukkit, coreprotect] + dependencies], "tests": tests,
        "native_acceptance": "UNPROVEN: build and standalone probes are not Bukkit/OPAC runtime proof"}
    (output / "evidence.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print("ERROR: " + str(error), file=sys.stderr)
        sys.exit(1)
