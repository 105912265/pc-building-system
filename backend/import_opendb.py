"""Safely import BuildCores OpenDB JSON directly into the PC Builder MySQL database.

Default: read-only preview. No CSV files involved.

Usage:
    python -m backend.import_opendb
    python -m backend.import_opendb --apply --max-records 30
    python -m backend.import_opendb --apply
    python -m backend.import_opendb --source-dir path/to/buildcores-open-db

Source: https://github.com/buildcores/buildcores-open-db
Attribution: BuildCores OpenDB, CC BY-NC-SA 4.0, https://creativecommons.org/licenses/by-nc-sa/4.0/
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import re
import sys
import tempfile
from typing import Any, Iterator
from urllib.request import Request, urlopen
import uuid
import zipfile

from backend.database import get_db_connection

SOURCE = "BuildCores OpenDB"
REPO_URL = "https://github.com/buildcores/buildcores-open-db"
ARCHIVE_URL = "https://codeload.github.com/buildcores/buildcores-open-db/zip/refs/heads/main"
LICENSE_URL = "https://creativecommons.org/licenses/by-nc-sa/4.0/"
CATEGORIES = ("CPU", "GPU", "Motherboard", "RAM", "Storage", "PSU")
# Limit the downloaded archive to guard against unexpected sizes.
MAX_ARCHIVE_BYTES = 250 * 1024 * 1024
MAX_JSON_BYTES = 500 * 1024


def clean_name(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


# Board-partner brands are distinct from GPU chipset manufacturers. OpenDB occasionally
# labels a board partner GPU as NVIDIA/AMD and puts the actual brand in metadata.name.
# Only infer from an explicit brand at the START of the name; otherwise trust metadata.
GPU_BOARD_BRANDS = {
    "ASUS", "MSI", "EVGA", "GIGABYTE", "ZOTAC", "PNY", "PALIT",
    "GAINWARD", "INNO3D", "GALAX", "KFA2", "SAPPHIRE", "XFX",
    "POWERCOLOR", "ASROCK", "COLORFUL", "MAXSUN", "YESTON",
    "ACER", "BIOSTAR", "SPARKLE", "LEADTEK", "MANLI", "VISIONTEK",
}
GPU_CHIPSET_BRANDS = {"NVIDIA", "AMD", "INTEL"}
GPU_BRAND_ALIASES = {"POWER COLOR": "POWERCOLOR", "POWER-COLOR": "POWERCOLOR"}


def leading_gpu_brand(name: str) -> tuple[str | None, str]:
    """Return a known GPU brand only when it appears at the start of a name."""
    labels = sorted(GPU_BOARD_BRANDS | GPU_CHIPSET_BRANDS | set(GPU_BRAND_ALIASES),
                    key=len, reverse=True)
    for label in labels:
        match = re.match(r"^" + re.escape(label) + r"(?:\s+|\s*[-:]\s*)", name, re.IGNORECASE)
        if match:
            return GPU_BRAND_ALIASES.get(label, label), name[match.end():].strip()
    return None, name


def normalize_vendor_model(category: str, manufacturer: str, source_name: str) -> tuple[str, str]:
    """Normalise vendor/model names without changing the original source snapshot."""
    vendor = clean_name(manufacturer)
    model = clean_name(source_name)
    if category == "GPU":
        brand, remainder = leading_gpu_brand(model)
        # Source sometimes records the chipset vendor followed by a board partner.
        if brand in GPU_CHIPSET_BRANDS:
            partner, partner_remainder = leading_gpu_brand(remainder)
            if partner in GPU_BOARD_BRANDS:
                vendor = partner
                model = partner_remainder
                return vendor, model or clean_name(source_name)
        # Source can also say manufacturer=NVIDIA while model starts EVGA/MSI etc.
        if brand in GPU_BOARD_BRANDS and vendor.upper() in GPU_CHIPSET_BRANDS:
            vendor = brand
            model = remainder
        else:
            # Remove a leading vendor once or twice (e.g. 'MSI MSI GeForce...').
            for _ in range(2):
                detected, rest = leading_gpu_brand(model)
                if detected and detected.casefold() == vendor.casefold():
                    model = rest
                else:
                    break
    else:
        # Non-GPU source names frequently already contain 'AMD', 'Intel', etc.
        for _ in range(2):
            match = re.match(r"^" + re.escape(vendor) + r"(?:\s+|\s*[-:]\s*)", model, re.IGNORECASE)
            if match:
                model = model[match.end():].strip()
            else:
                break
    return vendor, model or clean_name(source_name)


def name_key(category: str, manufacturer: str, name: str) -> tuple[str, str, str]:
    """Conservative matching: same category/vendor and identical normalized model.

    Strip the vendor once because source metadata.name often includes it,
    while the existing component.model usually omits it.
    """
    vendor = clean_name(manufacturer).casefold()
    model = clean_name(name).casefold()
    if model.startswith(vendor + " "):
        model = model[len(vendor) + 1:]
    model = re.sub(r"[^a-z0-9]+", "", model)
    return category.casefold(), vendor, model


def release_year(data: dict) -> int | None:
    value = data.get("metadata", {}).get("releaseYear")
    try:
        year = int(value)
    except (ValueError, TypeError):
        return None
    return year if 1990 <= year <= 2100 else None


def is_recent(category: str, data: dict, min_year: int) -> bool:
    """Curated modern product generations; do not trust release year alone."""
    metadata = data.get("metadata") or {}
    name = clean_name(metadata.get("name")).upper()
    year = release_year(data)
    # A strict age limit requires a documented release year.
    # Undated parts need manual verification rather than being treated as recent.
    if year is None or year < min_year or year > datetime.now().year + 1:
        return False

    if category == "CPU":
        # Restrict to desktop CPUs; common laptop suffixes are excluded.
        if re.search(r"\b(?:MOBILE|LAPTOP)\b|\b\d{4,5}(?:U|H|HS|HX|HK)\b", name):
            return False
        amd = re.search(r"\bRYZEN\s+(?:[3579]\s+)?[5-9]\d{3}[A-Z0-9]*\b", name)
        if amd:
            return True
        intel = re.search(r"\b(?:CORE|I[3579])\s+(?:I[3579][\s-]*)?(1[234])\d{3}[A-Z]*\b", name)
        if intel:
            return True
        # Core Ultra first generations; reject older processors.
        return bool(re.search(r"\bCORE\s+ULTRA\b", name))

    if category == "GPU":
        if any(marker in name for marker in ("LAPTOP", "MOBILE", "NOTEBOOK")):
            return False
        chipset = clean_name(data.get("chipset") or name).upper()
        return bool(
            # GTX 10 series (including 2017 GTX 1080 Ti) and GTX 16 series.
            re.search(r"\bGTX\s*(?:10|16)\d{2}(?:\s*(?:TI|SUPER))?\b", chipset)
            # RTX 20, 30, 40 and 50 series (and later if pattern updated).
            or re.search(r"\bRTX\s*[2345]\d{3}[A-Z0-9]*\b", chipset)
            # Radeon RX 5000, 6000, 7000, 9000 series.
            or re.search(r"\bRX\s*[5679]\d{3}[A-Z0-9]*\b", chipset)
        )

    if category == "Motherboard":
        socket = clean_name(data.get("socket")).upper().replace(" ", "")
        # LGA1200 is intentionally excluded to target Intel 12th-gen onwards.
        return socket in {"AM4", "AM5", "LGA1700", "LGA1851"}

    if category == "RAM":
        return str(data.get("ram_type", "")).upper() in {"DDR4", "DDR5"}

    if category == "Storage":
        return str(data.get("storage_type", "")).upper() == "SSD" and (
            bool(data.get("nvme")) or "SATA" in str(data.get("interface", "")).upper()
            or "PCIE" in str(data.get("interface", "")).upper()
        )

    if category == "PSU":
        try:
            watts = int(data.get("wattage") or 0)
        except (TypeError, ValueError):
            return False
        return watts >= 550 and watts <= 2000

    return False


def to_specs(category: str, source_data: dict, record_id: str) -> dict:
    """Maintain familiar keys used by Phase 3, plus original source fields."""
    metadata = source_data.get("metadata") or {}
    spec: dict[str, Any] = {
        "source": {
            "dataset": SOURCE,
            "id": record_id,
            "url": f"{REPO_URL}/blob/main/open-db/{category}/{record_id}.json",
            "licence": "CC BY-NC-SA 4.0",
            "licence_url": LICENSE_URL,
        },
        "opendb_data": {k: v for k, v in source_data.items()
                        if k not in {"identifiers", "opendb_id"}},
    }
    year = release_year(source_data)
    if year:
        spec["release_year"] = year
    link = (source_data.get("general_product_information") or {}).get("manufacturer_url")
    if link:
        spec["manufacturer_url"] = link
    if metadata.get("part_numbers"):
        spec["part_numbers"] = metadata["part_numbers"]

    if category == "CPU":
        cores = source_data.get("cores") or {}
        clocks = (source_data.get("clocks") or {}).get("performance") or {}
        cpu_specs = source_data.get("specifications") or {}
        if source_data.get("socket"):
            spec["socket"] = str(source_data["socket"]).replace(" ", "")
        if cores.get("total") is not None:
            spec["cores"] = cores["total"]
        if cores.get("threads") is not None:
            spec["threads"] = cores["threads"]
        if clocks.get("base") is not None:
            spec["base_clock_ghz"] = clocks["base"]
        if cpu_specs.get("tdp") is not None:
            spec["wattage"] = cpu_specs["tdp"]
        types = (cpu_specs.get("memory") or {}).get("types")
        if types:
            spec["ram_types"] = types
    elif category == "GPU":
        for k in ("chipset_manufacturer", "chipset", "memory_type"):
            if source_data.get(k):
                spec[k] = source_data[k]
        if source_data.get("memory") is not None:
            spec["vram_gb"] = source_data["memory"]
            spec["vram"] = f"{source_data['memory']}GB"
        if source_data.get("tdp") is not None:
            spec["wattage"] = source_data["tdp"]
        if source_data.get("length") is not None:
            spec["length_mm"] = source_data["length"]
    elif category == "Motherboard":
        memory = source_data.get("memory") or {}
        for k in ("socket", "form_factor", "chipset"):
            if source_data.get(k):
                spec[k] = source_data[k]
        if memory.get("ram_type"):
            spec["ram_type"] = memory["ram_type"]
            spec["memory"] = memory["ram_type"]
    elif category == "RAM":
        for k in ("ram_type", "speed", "capacity", "modules"):
            if source_data.get(k) is not None:
                spec[k] = source_data[k]
        if source_data.get("ram_type"):
            spec["type"] = source_data["ram_type"]
        if source_data.get("capacity") is not None:
            spec["capacity_gb"] = source_data["capacity"]
    elif category == "Storage":
        for k in ("storage_type", "form_factor", "interface"):
            if source_data.get(k):
                spec[k] = source_data[k]
        if source_data.get("capacity") is not None:
            spec["capacity_gb"] = source_data["capacity"]
    elif category == "PSU":
        if source_data.get("wattage") is not None:
            spec["wattage"] = f"{source_data['wattage']}W"
            spec["wattage_w"] = source_data["wattage"]
        for k in ("efficiency_rating", "modular", "form_factor"):
            if source_data.get(k) is not None:
                spec[k] = source_data[k]
    return spec


def combine_specs(old: Any, new: dict) -> dict:
    """Don't overwrite existing manual specifications; refresh source snapshot."""
    if isinstance(old, str):
        try:
            old = json.loads(old)
        except json.JSONDecodeError:
            old = {}
    merged = dict(old or {}) if isinstance(old, dict) else {}
    for key, value in new.items():
        if key in ("source", "opendb_data"):
            merged[key] = value
        elif key not in merged or merged[key] is None:
            merged[key] = value
    return merged


def iter_files_from_directory(root: Path, categories: set[str]) -> Iterator[tuple[str, str, dict]]:
    db_dir = root / "open-db"
    if not db_dir.is_dir():
        # Accept passing open-db/ directly.
        db_dir = root
    if not db_dir.is_dir():
        raise ValueError(f"Directory not found: {root}")
    for category in CATEGORIES:
        if category not in categories:
            continue
        folder = db_dir / category
        if not folder.is_dir():
            continue
        for path in sorted(folder.glob("*.json")):
            if path.stat().st_size > MAX_JSON_BYTES:
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8-sig"))
            except (OSError, ValueError):
                continue
            if isinstance(data, dict):
                yield category, path.stem, data


def iter_files_from_zip(archive: zipfile.ZipFile, categories: set[str]) -> Iterator[tuple[str, str, dict]]:
    for info in sorted(archive.infolist(), key=lambda f: f.filename):
        # e.g. buildcores-open-db-main/open-db/GPU/<uuid>.json
        segments = info.filename.split("/")
        if len(segments) < 3 or segments[-3] != "open-db":
            continue
        category, filename = segments[-2], segments[-1]
        if category not in categories or not filename.endswith(".json") or info.file_size > MAX_JSON_BYTES:
            continue
        try:
            with archive.open(info) as fp:
                data = json.load(io.TextIOWrapper(fp, encoding="utf-8-sig"))
        except (ValueError, UnicodeError, OSError, RuntimeError):
            continue
        if isinstance(data, dict):
            yield category, filename[:-5], data


def download_archive() -> Path:
    """Download once from GitHub into a temporary ZIP, never a permanent CSV."""
    print("Downloading BuildCores OpenDB from GitHub (temporary ZIP)...", flush=True)
    request = Request(ARCHIVE_URL, headers={"User-Agent": "PC-Builder-Phase5-Importer/1.0"})
    destination = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
    path = Path(destination.name)
    try:
        with destination, urlopen(request, timeout=90) as response:
            downloaded = 0
            while True:
                block = response.read(1024 * 1024)
                if not block:
                    break
                downloaded += len(block)
                if downloaded > MAX_ARCHIVE_BYTES:
                    raise RuntimeError("Archive exceeds 250 MB safety limit")
                destination.write(block)
        return path
    except Exception:
        path.unlink(missing_ok=True)
        raise


def normalize(category: str, stem: str, data: dict, min_year: int) -> dict | None:
    rid = str(data.get("opendb_id", ""))
    try:
        rid = str(uuid.UUID(rid))
    except (ValueError, AttributeError, TypeError):
        return None
    if rid != stem.lower():
        return None
    meta = data.get("metadata")
    if not isinstance(meta, dict):
        return None
    name = clean_name(meta.get("name"))
    manufacturer = clean_name(meta.get("manufacturer"))
    if not name or not manufacturer or not is_recent(category, data, min_year):
        return None
    manufacturer, name = normalize_vendor_model(category, manufacturer, name)
    if len(name) > 150 or len(manufacturer) > 100:
        return None
    return {
        "source_id": rid,
        "category": category,
        "manufacturer": manufacturer,
        "model": name,
        "specifications": to_specs(category, data, rid),
    }


def schema_ready(connection) -> bool:
    cursor = connection.cursor()
    try:
        cursor.execute("""SELECT IS_NULLABLE FROM information_schema.COLUMNS
                          WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME='component'
                          AND COLUMN_NAME='price'""")
        price_row = cursor.fetchone()
        cursor.execute("""SELECT COUNT(*) FROM information_schema.TABLES
                          WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='component_source'""")
        mapping_exists = cursor.fetchone()[0] > 0
        return price_row is not None and price_row[0] == 'YES' and mapping_exists
    finally:
        cursor.close()


def existing_records(connection) -> tuple[dict, dict, bool]:
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT component_id, category, manufacturer, model, specifications FROM component")
        existing = {}
        for row in cursor.fetchall():
            key = name_key(row["category"], row["manufacturer"], row["model"])
            # If two local components share a normalized name, keep first (conservative match).
            existing.setdefault(key, row)
        mapping = {}
        cursor.execute("""SELECT COUNT(*) AS count FROM information_schema.TABLES
                          WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='component_source'""")
        has_mapping = cursor.fetchone()["count"] > 0
        if has_mapping:
            cursor.execute("""SELECT source_record_id, component_id
                              FROM component_source WHERE source_name=%s""", (SOURCE,))
            mapping = {r["source_record_id"]: r["component_id"] for r in cursor.fetchall()}
        return existing, mapping, has_mapping
    finally:
        cursor.close()


def plan_rows(source_rows: Iterator[tuple[str, str, dict]], existing: dict,
              mapping: dict, min_year: int, max_records: int | None) -> tuple[list[tuple[str, dict, int | None]], Counter, dict]:
    plan: list[tuple[str, dict, int | None]] = []
    stats = Counter()
    sample: dict[str, list[str]] = {category: [] for category in CATEGORIES}
    seen_ids = set()
    seen_names = set()
    for category, stem, data in source_rows:
        stats["source_files_read"] += 1
        row = normalize(category, stem, data, min_year)
        if not row:
            stats["filtered_or_invalid"] += 1
            continue
        rid = row["source_id"]
        key = name_key(category, row["manufacturer"], row["model"])
        if rid in seen_ids or (key in seen_names and rid not in mapping):
            stats["duplicate_source"] += 1
            continue
        seen_ids.add(rid)
        seen_names.add(key)
        target = mapping.get(rid)
        if target is not None:
            action = "update_linked"
        elif key in existing:
            target = existing[key]["component_id"]
            action = "link_existing"
        else:
            action = "insert"
        stats[action] += 1
        plan.append((action, row, target))
        if len(sample[category]) < 4:
            sample[category].append(row["model"])
        if max_records and len(plan) >= max_records:
            break
    return plan, stats, sample


def apply_plan(connection, plan: list[tuple[str, dict, int | None]]) -> Counter:
    """All-or-nothing transaction; never delete components or reset IDs."""
    # Preview SELECTs may have opened an implicit transaction (autocommit=False).
    # End it before starting the atomic write transaction.
    connection.rollback()
    cursor = connection.cursor()
    counts = Counter()
    try:
        connection.start_transaction()
        if not schema_ready(connection):
            raise RuntimeError("Schema migration missing. Run backend/migrations/001_opendb.sql in Workbench.")
        # Read all known component ID->specs, including linked and manually matched.
        ids = {target for _, _, target in plan if target is not None}
        current = {}
        for cid in ids:
            cursor.execute("SELECT specifications FROM component WHERE component_id=%s", (cid,))
            result = cursor.fetchone()
            if not result:
                raise RuntimeError(f"Linked component_id {cid} no longer exists")
            current[cid] = result[0]
        for action, row, target in plan:
            if action == "insert":
                cursor.execute(
                    """INSERT INTO component (category, manufacturer, model, price, release_date, specifications)
                       VALUES (%s,%s,%s,NULL,NULL,%s)""",
                    (row["category"], row["manufacturer"], row["model"],
                     json.dumps(row["specifications"], ensure_ascii=False)),
                )
                target = cursor.lastrowid
            else:
                merged = combine_specs(current[target], row["specifications"])
                cursor.execute("UPDATE component SET specifications=%s WHERE component_id=%s",
                               (json.dumps(merged, ensure_ascii=False), target))
                current[target] = json.dumps(merged, ensure_ascii=False)
            cursor.execute(
                """INSERT INTO component_source (source_name, source_record_id, component_id)
                   VALUES (%s,%s,%s)
                   ON DUPLICATE KEY UPDATE component_id=VALUES(component_id), last_imported_at=CURRENT_TIMESTAMP""",
                (SOURCE, row["source_id"], target),
            )
            counts[action] += 1
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description="Preview/import modern BuildCores components into MySQL")
    parser.add_argument("--apply", action="store_true", help="Write to MySQL (default: preview only)")
    parser.add_argument("--max-records", type=int, default=None, help="Cap qualifying components for a small trial")
    parser.add_argument("--min-year", type=int, default=2017, help="Oldest allowed verified release year (default: 2017)")
    parser.add_argument("--categories", nargs="+", choices=CATEGORIES, default=list(CATEGORIES))
    parser.add_argument("--find-model", type=str, default=None,
                        help="Only preview/import source products whose name or chipset matches this text")
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--source-dir", type=Path, help="Local OpenDB checkout (for testing/offline use)")
    source.add_argument("--archive", type=Path, help="Already downloaded OpenDB ZIP")
    args = parser.parse_args()
    if args.max_records is not None and args.max_records < 1:
        parser.error("--max-records must be >= 1")
    if args.min_year < 2015 or args.min_year > datetime.now().year + 1:
        parser.error("--min-year must be between 2015 and next year")

    temp_archive = None
    try:
        archive_path = args.archive
        if args.source_dir:
            source_rows = list(iter_files_from_directory(args.source_dir, set(args.categories)))
        else:
            if archive_path is None:
                temp_archive = download_archive()
                archive_path = temp_archive
            with zipfile.ZipFile(archive_path) as zipfile_obj:
                source_rows = list(iter_files_from_zip(zipfile_obj, set(args.categories)))
        print(f"Read {len(source_rows)} source JSON records in requested categories.")
        if not source_rows:
            raise RuntimeError("No component files found; inspect --source-dir or archive structure")
        if args.find_model:
            # Ignore spacing and punctuation (e.g., GTX1080Ti vs GTX 1080 Ti).
            query = re.sub(r"[^a-z0-9]+", "", args.find_model.casefold())
            source_rows = [
                (cat, stem, data) for cat, stem, data in source_rows
                if query in re.sub(
                    r"[^a-z0-9]+", "", (
                        clean_name((data.get("metadata") or {}).get("name")) + " " +
                        clean_name(data.get("chipset"))
                    ).casefold())
            ]
            print(f"Source records matching {args.find_model!r}: {len(source_rows)}")
        connection = get_db_connection()
        try:
            existing, mapping, has_mapping = existing_records(connection)
            plan, stats, sample = plan_rows(iter(source_rows), existing, mapping,
                                             args.min_year, args.max_records)
            print("\n=== OpenDB import PREVIEW ===")
            print(f"Current database components (distinct name keys): {len(existing)}")
            print(f"Import mapping table present: {has_mapping}")
            print(f"Allowed categories: {', '.join(args.categories)}")
            print(f"Minimum known release year: {args.min_year}")
            print(f"Qualified records in plan: {len(plan)}")
            print("\n=== ELIGIBLE COUNTS BY CATEGORY ===")
            # A record is eligible whether it needs insertion or is already known in MySQL.
            by_category = {category: Counter() for category in args.categories}
            for action, record, _ in plan:
                by_category[record["category"]][action] += 1
            for category in args.categories:
                counts = by_category[category]
                total = sum(counts.values())
                print(
                    f"  {category}: {total} eligible "
                    f"({counts['insert']} new, {counts['link_existing']} existing matches, "
                    f"{counts['update_linked']} previously imported)"
                )
            print("\n=== OVERALL ACTIONS ===")
            for key in ("insert", "link_existing", "update_linked", "duplicate_source",
                        "filtered_or_invalid"):
                print(f"{key}: {stats[key]}")
            for category in args.categories:
                if sample[category]:
                    print(f"  {category}: " + "; ".join(sample[category]))
            if args.find_model and plan:
                print("All qualified matches:")
                for action, row, target in plan:
                    print(f"  {action}: {row['manufacturer']} {row['model']}")
            print("\nSource: BuildCores OpenDB — CC BY-NC-SA 4.0")
            print("Note: imported products have UNKNOWN prices (NULL), not $0.")
            if args.apply:
                if not plan:
                    print("No matching products to import.")
                    return
                counts = apply_plan(connection, plan)
                print("\nIMPORT COMMITTED:", dict(counts))
                print("No existing prices, component IDs, builds or reviews were deleted.")
            else:
                print("\nDRY RUN ONLY: No database records were changed.")
                if not schema_ready(connection):
                    print("Before --apply, run backend/migrations/001_opendb.sql in Workbench.")
        finally:
            connection.close()
    finally:
        if temp_archive:
            temp_archive.unlink(missing_ok=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Import stopped: {exc}", file=sys.stderr)
        sys.exit(1)
