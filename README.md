# Portfolio Metadata

The portfolio's content lives as a set of small, individually editable JSON files
inside the [json/](json/) folder. The script
[validate_and_combine_json.py](validate_and_combine_json.py) validates those files
and merges them into a single `main.json` that the front-end consumes.

The portfolio's *colours* live separately in [theme.json](theme.json), which the
front-end fetches as its own endpoint — see [Theme](#theme) below.

## Access Links

| Document | URL |
|---|---|
| Content | https://raw.githubusercontent.com/portfolio-sawarni/metadata/refs/heads/main/main.json |
| Theme | https://raw.githubusercontent.com/portfolio-sawarni/metadata/refs/heads/main/theme.json |

## Layout

```
portfolio-metadata/
├── json/
│   ├── portfolio.json        # entry point — maps sections to their JSON files
│   ├── skills.json           # master list of skills (each has a unique_id)
│   ├── domains.json          # master list of domains (each has a unique_id)
│   ├── projects.json
│   ├── experience.json
│   ├── certifications.json
│   ├── badges.json
│   ├── achievements.json
│   ├── hobbies.json
│   └── social_media.json
├── validate_and_combine_json.py
├── main.json                 # generated output (do not edit by hand)
└── theme.json                # colour system (edited by hand)
```

### `portfolio.json`

This is the entry point. Each key is a section of the portfolio, and its value is
either:

- a **string** ending in `.json` — the file whose contents get inlined,
- a **nested object** whose string `.json` values are likewise inlined, or
- a **literal value** (string/object) that is copied through as-is.

## What the script does

Running the script performs two phases: **validation**, then **combination**. If
any validation fails, nothing is written and every issue is reported.

### Validations

1. **Valid JSON** — every `*.json` file in [json/](json/) parses correctly.
2. **Referenced files exist** — every `.json` file named in `portfolio.json`
   (top-level or nested) is present in the folder.
3. **Unique ids** — every record in `skills.json` and `domains.json` has a
   non-empty `unique_id`, and no id is repeated within a file.
4. **Skill references** — every skill id used in `experience.json`,
   `certifications.json`, `badges.json`, and `projects.json` (in each file's
   `skills` field) exists as a `unique_id` in `skills.json`.
5. **Domain references** — every domain id referenced exists as a `unique_id` in
   `domains.json`. Note the field name differs by file: `projects.json` uses a
   list field `domains`, while `certifications.json` and `badges.json` use a
   single-string field `domain`.
6. **Experience years** — in `experience.json`, `startYear` must be a four-digit
   year (`YYYY`); `endYear` must be `YYYY` or the string `"Present"`; and when
   `endYear` is a concrete year it must not be earlier than `startYear`.

Reference fields are lenient: a single string, a list of strings, or an empty
string/list are all accepted, and empty values are treated as "no reference".

### Combination

When all validations pass, the script walks `portfolio.json`, inlines every
referenced `.json` file (top-level and one level of nesting), and writes the
merged result to `main.json` next to the script (indented, UTF-8, non-ASCII
preserved).

## How to run

Requires Python 3 (standard library only — no dependencies to install).

```bash
cd portfolio-metadata
python3 validate_and_combine_json.py
```

On success:

```
All validations passed. Wrote combined output to '.../portfolio-metadata/main.json'.
```

On failure, `main.json` is left untouched and each problem is listed:

```
Validation failed with 2 issue(s):
  - Unknown skill 'python3' in projects.json[0] (not found in skills.json).
  - experience.json[1] has invalid startYear 'None' (expected 'YYYY').
```

Paths are resolved relative to the script's own location, so it can be run from
any working directory.

## Theme

[theme.json](theme.json) holds every colour the site paints with. It is written
by hand and served as-is — it is not part of the combine script, so editing it
takes effect as soon as the file is published. Changing a hex here re-skins the
front-end with no code change.

| Field | What it colours |
|---|---|
| `tokens` | Named colours mirrored into CSS custom properties (`--color-<key>`): text (`ink`, `ink-2`…`ink-4`), backgrounds (`bg`, `dark-bg`, `surface`…), and accents (`accent`, `teal`, `rose`…). |
| `skill_palette` | The rotating chip palette. Skills take a colour by their declared position in `skills.json`, so order — not this list — decides which skill gets which colour. |
| `domain_colors` | Fixed domain colours keyed by `unique_id` from `domains.json`. |
| `domain_fallback_palette_indices` | Positions in `skill_palette` used for domains `domain_colors` doesn't name. |
| `default_accent` | Accent for an achievement emblem rendered without a crest. |
| `achievement_crests` | Achievement emblem gradients, each `[light, mid, deep]`, rotating by achievement order. |

Values are CSS colours; plain 6-digit hex is the convention, and 8-digit hex
(`#rrggbbaa`) works where a baked-in alpha is wanted. Translucent shadows and
glass fills are derived from `tokens` in the front-end, so they follow along
without needing their own entries.

Omitting a token is not an error: anything the document leaves out keeps the
front-end's white placeholder, which is also what shows while the request is in
flight.
