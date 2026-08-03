# Portfolio Metadata

This repository is the portfolio's content store. It holds three things:

- the **content** — small, individually editable JSON files in [json/](json/),
  merged by a script into a single `main.json`,
- the **assets** those files point at — images, documents and article bodies in
  [assets/](assets/) and [articles/](articles/),
- the **theme** — [theme.json](theme.json), the colour system, a handful of
  display tunables, and the site's fixed display copy.

`main.json` and `theme.json` are served straight from the repository over raw
GitHub URLs and fetched by the site at startup. Nothing here is built or
deployed; publishing a change means committing it.

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
├── assets/
│   ├── images/               # badges, certificates, dp, hobbies, project shots,
│   │                         #   social media logos — one folder per kind
│   └── resume/               # PDFs
├── articles/                 # article bodies as Markdown, one file each
├── validate_and_combine_json.py
├── main.json                 # generated output (do not edit by hand)
├── theme.json                # colour system + display copy (edited by hand)
└── theme-format.txt          # field-by-field reference for theme.json
```

### `portfolio.json`

This is the entry point. Each key is a section of the portfolio, and its value is
either:

- a **string** ending in `.json` — the file whose contents get inlined,
- a **nested object** whose string `.json` values are likewise inlined, or
- a **literal value** (string/object) that is copied through as-is.

The `about` and `contact` blocks are the literal case: they are written inline in
`portfolio.json` rather than living in files of their own.

### Assets

Asset paths are written relative to the repository root — for example
`/assets/images/dp/sawarni_5.png` — and the script expands them into full raw
GitHub URLs on the way into `main.json`. Values that are already absolute
(`http://`, `https://`) are left alone, and empty values stay empty.

The keys treated as asset paths are:

| Kind | Keys |
|---|---|
| Images | `display_picture`, `picture`, `pictures`, `logo` |
| Documents | `resume` |
| Article bodies | `content` |

Each may hold a single path or a list of paths.

### Articles

The writing index is optional. When present it is `json/articles.json`, wired
into `portfolio.json` like any other section, with each record carrying an `id`,
a `date` and a `content` path pointing at a Markdown file in [articles/](articles/).
There are no articles at the moment, and the script simply skips the
article validations when the file is absent.

## What the script does

[validate_and_combine_json.py](validate_and_combine_json.py) performs two
phases: **validation**, then **combination**. If any validation fails, nothing is
written and every issue is reported.

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
7. **Article dates** — `date` in `articles.json` is `DD/MM/YYYY` and must be a
   real calendar date.
8. **Article ids** — every record in `articles.json` has an `id`, and no two
   share one. The site routes `/article/<id>` by it.

Reference fields are lenient: a single string, a list of strings, or an empty
string/list are all accepted, and empty values are treated as "no reference".

Asset paths are not validated — a path that names a missing file passes, and
surfaces as a broken image on the page instead.

### Combination

When all validations pass, the script walks `portfolio.json`, inlines every
referenced `.json` file (top-level and one level of nesting), expands the asset
paths described above, and writes the merged result to `main.json` next to the
script (indented, UTF-8, non-ASCII preserved).

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

[theme.json](theme.json) holds every colour the site paints with, a small set of
display tunables, and the fixed copy it prints. It is written by hand and served
as-is — it is not part of the combine script, so an edit takes effect as soon as
the file is published. Changing a hex here re-skins the site with no code change;
changing a string re-voices it.

[theme-format.txt](theme-format.txt) is the field-by-field reference; the table
below is the map.

| Field | What it controls |
|---|---|
| `version`, `name`, `description` | Schema version and human labels. Not rendered. |
| `navbar` | The nav's `cta_label` and its `sections` list — each an `id` (a home-page anchor, or a `/route`) and a display `name`. |
| `tokens` | Named colours mirrored into CSS custom properties (`--color-<key>`, plus a `-rgb` companion for translucent tints): text (`ink`, `ink-2`…`ink-4`), backgrounds (`bg`, `dark-bg`, `surface`…), and accents (`accent`, `teal`, `rose`…). |
| `skill_palette` | The rotating chip palette. Skills take a colour by their declared position in `skills.json`, so order — not this list — decides which skill gets which colour. |
| `domain_colors` | Fixed domain colours keyed by `unique_id` from `domains.json`. |
| `domain_fallback_palette_indices` | Positions in `skill_palette` used for domains `domain_colors` doesn't name. |
| `default_accent` | Accent for an achievement emblem rendered without a crest. |
| `project_covers`, `achievement_crests`, `certificate_crests` | Gradients for project covers and for achievement/certificate emblems, each `[light, mid, deep]`, rotating by the item's order. |
| `article_accents` | Accents for the writing index — ordinal, kicker and arrow on each row — rotating by article order. Darker than `skill_palette`, since these are text on the page rather than white text on a chip. |
| `skills_marquee_speed`, `domain_bounce_speed`, `dark_fade_ms` | Motion speeds for the skills marquee, the domain bounce, and the dark-section fade. |
| `home_skills_limit`, `certificates_preview_count`, `carousel_focus_dots` | How many skill chips a home-page card shows (`-1` for all), how many certificates preview on the home page, and how many carousel dots stay at full opacity. |
| `hero_portrait_opacity` | Opacity of the hero portrait. |
| `strings` | Fixed display copy — kickers, titles, intros, labels and closing lines. See below. |

Colour values are CSS colours; plain 6-digit hex is the convention, and 8-digit
hex (`#rrggbbaa`) works where a baked-in alpha is wanted. Translucent shadows and
glass fills are derived from `tokens`, so they follow along without needing their
own entries. Nothing here controls layout, spacing, blur radii or shadow
geometry.

Omitting a key is not an error: anything the document leaves out keeps the site's
placeholder, which is also what shows while the request is in flight.

### Strings

`strings` carries the wording that belongs to the *design* rather than to the
portfolio's content: numbered kickers (`02 — Experience`), section and page
titles, the paragraph under a title, button and filter labels, and the messages
shown when there is nothing to print. It is grouped by the section or route that
renders it — `common`, `hero`, `experience`, `projects`, `certificates`,
`achievements`, `trophy_wall`, `beyond_work`, `articles`, `footer`, `chat`,
`status` — and the groups draw from a shared key vocabulary:

| Key | Where it shows |
|---|---|
| `kicker` | The mono, uppercase line above the title — on the home page, and on the route that section leads to. |
| `title` | The home page section heading. |
| `detail_title` | The heading on that route. |
| `detail_intro` | The paragraph directly under that heading. |
| `detail_outro` | The closing line at the foot of that route. |
| `empty_body` | Shown when there is nothing to render — a filter matching no rows, or content that failed to load. |
| `*_label` | Buttons, links, filters and accessible names. |

A group carries only the keys it renders. `common` is the shared set every
section can fall back on — `back_label`, `filter_label`, `previous_label` and
friends, plus `no_data`, the placeholder rendered for any string the site asks
for that this document does not carry. `experience` and `projects` are a heading
over a list on the home page, so alongside `kicker`/`title` they carry
`detail_outro` — the detail route takes its own heading from the job or project.
`trophy_wall` and `beyond_work` are routes of their own, so `title` belongs to
the home page CTA and the `detail_*` set to the page, with `kicker` printed on
both. `certificates` adds the filter labels and `empty_title`/`empty_body` for
the filtered archive. `articles` heads the writing index with `kicker`/`title`
and `detail_intro`, plus search, sort and count labels and four keys for the
states with nothing to print — `empty_body` when the content document carries no
`articles` key, `not_found_body` when a `/article/<id>` URL names one the index
does not have, `search_empty_body` when the search matches nothing, and
`content_empty_body` when an article's `content` URL does not answer. `footer`
covers the message form — its label, placeholders, send button and the empty and
sent messages. `chat` covers the assistant widget: placeholder, online/offline
status and the body shown while it is asleep. `status` is the loading and error
frame: the line under the loading mark, the message when content fails to
arrive, and the retry affordance.

The one exception is `trophy_wall.stat_badges` / `trophy_wall.stat_platforms`,
the labels under that page's two counters — they name specific counters, so
there is no shared key for them.

Anything not here stays in the code on purpose: form field names and the
placeholder text that stands in for a blank content field. Names, blurbs, roles
and write-ups all come from the content document instead.

Omitting a string is not an error either — the same default wording ships in the
code and is used per key, so a partial `strings` block is fine.
