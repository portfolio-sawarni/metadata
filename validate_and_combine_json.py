import json
import os
import re

# Directory containing all the individual JSON files.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_DIR = os.path.join(BASE_DIR, "json")
PORTFOLIO_FILE = "portfolio.json"
# main.json is written outside the json folder, next to this script.
OUTPUT_PATH = os.path.join(BASE_DIR, "main.json")
DEFAULT_IMAGE_PATH = "https://raw.githubusercontent.com/portfolio-sawarni/metadata/refs/heads/main/"

# Keys anywhere in the combined output that hold image paths. Values may be a
# single path (string) or a list of paths.
IMAGE_KEYS = {"display_picture", "picture", "pictures"}

# Keys holding document paths (PDFs and the like). Same handling as images:
# relative paths get the metadata base URL prefixed.
DOCUMENT_KEYS = {"resume"}

# Every key whose value should be expanded into a full URL.
ASSET_KEYS = IMAGE_KEYS | DOCUMENT_KEYS

# Files whose records reference skills, and the field holding the skill ids.
SKILL_SOURCES = {
    "experience.json": "skills",
    "certifications.json": "skills",
    "badges.json": "skills",
    "projects.json": "skills",
}

# Files whose records reference domains, and the field holding the domain id(s).
# Note the field name differs: projects uses a list ("domains"), while
# certifications and badges use a single string ("domain").
DOMAIN_SOURCES = {
    "badges.json": "domain",
    "certifications.json": "domain",
    "projects.json": "domains",
}


def _path(filename):
    """Return the absolute path to a file inside the json directory."""
    return os.path.join(JSON_DIR, filename)


def _load_json(filename):
    """Load and parse a JSON file from the json directory."""
    with open(_path(filename), "r", encoding="utf-8") as handle:
        return json.load(handle)


def _as_id_list(value):
    """Normalise a reference field into a list of ids.

    Accepts a single string, a list of strings, or an empty string/list.
    Empty strings are dropped so that empty references are treated as "none".
    """
    if isinstance(value, list):
        return [item for item in value if item != ""]
    if isinstance(value, str):
        return [value] if value != "" else []
    return []


def validate_json_files(errors):
    for filename in sorted(os.listdir(JSON_DIR)):
        if not filename.endswith(".json"):
            continue
        try:
            _load_json(filename)
        except json.JSONDecodeError as exc:
            errors.append("Invalid JSON in '{}': {}".format(filename, exc))
        except OSError as exc:
            errors.append("Could not read '{}': {}".format(filename, exc))


def validate_referenced_files_exist(errors, portfolio):
    for key, value in portfolio.items():
        referenced = []
        if isinstance(value, str) and value.endswith(".json"):
            referenced.append(value)
        elif isinstance(value, dict):
            referenced.extend(
                item for item in value.values()
                if isinstance(item, str) and item.endswith(".json")
            )
        for filename in referenced:
            if not os.path.isfile(_path(filename)):
                errors.append(
                    "portfolio.json references '{}' (key '{}') "
                    "but it is missing from the json folder.".format(filename, key)
                )


def validate_unique_ids(errors):
    """Every record in skills.json and domains.json must carry a unique_id.

    Nothing downstream can reference — or colour — a record without one, so a
    missing, blank or duplicated id is an error rather than a warning.
    """
    for filename in ("skills.json", "domains.json"):
        try:
            records = _load_json(filename)
        except (json.JSONDecodeError, OSError):
            continue  # Reported by validate_json_files.

        if not isinstance(records, list):
            errors.append("{} must be an array of objects.".format(filename))
            continue

        seen = set()
        for index, record in enumerate(records):
            if not isinstance(record, dict):
                errors.append("{}[{}] is not an object.".format(filename, index))
                continue

            unique_id = record.get("unique_id")
            if not isinstance(unique_id, str) or unique_id.strip() == "":
                errors.append(
                    "{}[{}] is missing a unique_id "
                    "(found '{}').".format(filename, index, unique_id)
                )
                continue

            if unique_id in seen:
                errors.append(
                    "{}[{}] repeats unique_id '{}'.".format(filename, index, unique_id)
                )
            seen.add(unique_id)


def validate_skill_references(errors):
    try:
        skills = _load_json("skills.json")
    except (json.JSONDecodeError, OSError):
        return  # Reported by validate_json_files.

    valid_ids = {entry.get("unique_id") for entry in skills}

    for filename, field in SKILL_SOURCES.items():
        try:
            records = _load_json(filename)
        except (json.JSONDecodeError, OSError):
            continue  # Reported by validate_json_files.
        for index, record in enumerate(records):
            for skill_id in _as_id_list(record.get(field, [])):
                if skill_id not in valid_ids:
                    errors.append(
                        "Unknown skill '{}' in {}[{}] "
                        "(not found in skills.json).".format(skill_id, filename, index)
                    )


def validate_domain_references(errors):
    try:
        domains = _load_json("domains.json")
    except (json.JSONDecodeError, OSError):
        return  # Reported by validate_json_files.

    valid_ids = {entry.get("unique_id") for entry in domains}

    for filename, field in DOMAIN_SOURCES.items():
        try:
            records = _load_json(filename)
        except (json.JSONDecodeError, OSError):
            continue  # Reported by validate_json_files.
        for index, record in enumerate(records):
            for domain_id in _as_id_list(record.get(field, [])):
                if domain_id not in valid_ids:
                    errors.append(
                        "Unknown domain '{}' in {}[{}] "
                        "(not found in domains.json).".format(domain_id, filename, index)
                    )


def validate_experience_years(errors):
    """
    ``startYear`` must be a four-digit year (YYYY). ``endYear`` may be a
    four-digit year or the string 'Present'. When ``endYear`` is a year it must
    be greater than or equal to ``startYear``.
    """
    year_pattern = re.compile(r"^\d{4}$")

    try:
        records = _load_json("experience.json")
    except (json.JSONDecodeError, OSError):
        return  # Reported by validate_json_files.

    for index, record in enumerate(records):
        start = record.get("startYear")
        end = record.get("endYear")

        start_valid = isinstance(start, str) and year_pattern.match(start)
        if not start_valid:
            errors.append(
                "experience.json[{}] has invalid startYear '{}' "
                "(expected 'YYYY').".format(index, start)
            )

        end_valid = end == "Present" or (
            isinstance(end, str) and year_pattern.match(end)
        )
        if not end_valid:
            errors.append(
                "experience.json[{}] has invalid endYear '{}' "
                "(expected 'YYYY' or 'Present').".format(index, end)
            )

        # Only compare when both are concrete years.
        if start_valid and end_valid and end != "Present" and int(end) < int(start):
            errors.append(
                "experience.json[{}] has endYear '{}' earlier than "
                "startYear '{}'.".format(index, end, start)
            )


def _resolve_asset_path(value):
    """Prefix a relative asset path with the metadata base URL.

    Absolute URLs (http/https) are kept as-is, and empty values stay empty.
    """
    if not isinstance(value, str) or value == "":
        return value
    if value.lower().startswith(("http://", "https://")):
        return value
    return DEFAULT_IMAGE_PATH + value.lstrip("/")


def resolve_asset_paths(data):
    """Walk the combined data and expand every asset path in ASSET_KEYS."""
    if isinstance(data, dict):
        resolved = {}
        for key, value in data.items():
            if key in ASSET_KEYS:
                if isinstance(value, list):
                    resolved[key] = [_resolve_asset_path(item) for item in value]
                else:
                    resolved[key] = _resolve_asset_path(value)
            else:
                resolved[key] = resolve_asset_paths(value)
        return resolved
    if isinstance(data, list):
        return [resolve_asset_paths(item) for item in data]
    return data


def combine(portfolio):
    combined = {}
    for key, value in portfolio.items():
        if isinstance(value, str) and value.endswith(".json"):
            combined[key] = _load_json(value)
        elif isinstance(value, dict):
            combined[key] = {
                inner_key: (
                    _load_json(inner_value)
                    if isinstance(inner_value, str) and inner_value.endswith(".json")
                    else inner_value
                )
                for inner_key, inner_value in value.items()
            }
        else:
            combined[key] = value

    combined = resolve_asset_paths(combined)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as handle:
        json.dump(combined, handle, indent=4, ensure_ascii=False)
    return OUTPUT_PATH


def main():
    errors = []

    # Validation 1 first: everything else depends on valid JSON.
    validate_json_files(errors)

    # Load portfolio.json for the remaining validations.
    portfolio = None
    try:
        portfolio = _load_json(PORTFOLIO_FILE)
    except (json.JSONDecodeError, OSError) as exc:
        errors.append("Could not load '{}': {}".format(PORTFOLIO_FILE, exc))

    if portfolio is not None:
        validate_referenced_files_exist(errors, portfolio)
    validate_unique_ids(errors)
    validate_skill_references(errors)
    validate_domain_references(errors)
    validate_experience_years(errors)

    if errors:
        print("Validation failed with {} issue(s):".format(len(errors)))
        for issue in errors:
            print("  - {}".format(issue))
        return

    output_path = combine(portfolio)
    print("All validations passed. Wrote combined output to '{}'.".format(output_path))


if __name__ == "__main__":
    main()
