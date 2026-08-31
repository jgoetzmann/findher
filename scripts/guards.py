#!/usr/bin/env python3
"""The guards. Every refusal in this skill is a function in this file.

Prose refusals get argued past. These fail the build.

Each denylist is named, non-empty, and checked for emptiness by
`check_denylists`, because a preflight that ships with an empty list passes
vacuously while printing a green line. That is the defect this file exists to
catch, sold as a feature.
"""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Iterable, NamedTuple

ROOT = Path(__file__).resolve().parent.parent


class Finding(NamedTuple):
    """One refusal. `rule` names the check so a selftest can target it."""

    guard: str
    rule: str
    detail: str
    because: str

    def __str__(self) -> str:
        return f"[{self.guard}/{self.rule}] {self.detail}\n    why: {self.because}"


# --------------------------------------------------------------------------
# Denylists. Named, non-empty, and load-bearing.
# --------------------------------------------------------------------------

# Words that bind a phrase to one human being.
PERSON_CUES = (
    "her name", "his name", "their name", "name is", "name's", "named",
    "goes by", "she works", "he works", "she studies", "he studies",
    "she sits", "he sits", "she lives", "he lives", "she said", "he said",
    "we matched", "i met her", "i met him", "this girl", "that girl",
    "this guy", "that guy", "this woman", "that woman", "this man", "that man",
    "the one in", "the one at", "the one from", "the one who", "the girl who",
    "the guy who", "the barista", "my ex", "her instagram", "his instagram",
    "her profile", "his profile",
)

# Words that name one building, one org, or one slot on a timetable.
INSTITUTIONS = (
    "university", "college", "campus", "school", "academy", "institute",
    "hospital", "clinic", "firm", "agency", "startup", "office", "lab",
    "department", "faculty", "dorm", "residence", "starbucks", "target",
    "walmart", "costco", "trader", "whole", "amazon", "google", "microsoft",
    "section", "seminar", "lecture", "tutorial", "cohort", "shift",
)

# Rooms, not people. A capitalised phrase holding one of these is a scene.
SCENE_NOUNS = (
    "club", "society", "night", "group", "league", "team", "choir", "band",
    "orchestra", "ensemble", "meetup", "collective", "guild", "circle",
    "crew", "jam", "run", "ride", "workshop", "festival", "union", "studio",
    "gym", "cafe", "café", "bar", "pub", "church", "temple", "synagogue",
    "mosque", "library", "market", "co-op", "coop", "class", "course",
    "series", "screening", "screenings", "open", "mic", "trivia", "chorus",
    "hall", "centre", "center", "space", "shop", "store", "park", "range",
    "court", "rink", "pool", "track", "wall", "kitchen", "garden",
)

# The vocabulary an honest seed is written in. A token in here is not a name.
COMMON_WORDS = (
    "a", "an", "the", "and", "or", "but", "not", "no", "so", "if", "of", "to",
    "in", "on", "at", "for", "with", "without", "from", "by", "about", "into",
    "over", "under", "than", "then", "that", "this", "these", "those", "who",
    "whom", "whose", "which", "what", "when", "where", "how", "why", "is",
    "are", "was", "were", "be", "been", "being", "has", "have", "had", "do",
    "does", "did", "can", "could", "would", "should", "will", "want", "wants",
    "wanted", "like", "likes", "liked", "love", "loves", "prefer", "prefers",
    "someone", "somebody", "anyone", "person", "people", "woman", "women",
    "man", "men", "guy", "guys", "girl", "girls", "partner", "friend",
    "friends", "grad", "graduate", "student", "students", "job", "work",
    "works", "working", "career", "real", "kind", "kinda", "sort", "quiet",
    "loud", "funny", "smart", "clever", "curious", "patient", "warm", "calm",
    "chill", "serious", "silly", "weird", "unusual", "nice", "good", "great",
    "long", "short", "old", "older", "young", "younger", "age", "years",
    "year", "live", "lives", "living", "music", "live", "film", "films",
    "movie", "movies", "book", "books", "reads", "reading", "read", "cook",
    "cooks", "cooking", "food", "coffee", "tea", "beer", "wine", "walk",
    "walks", "walking", "hike", "hikes", "hiking", "bike", "bikes", "biking",
    "run", "runs", "running", "swim", "swims", "climb", "climbs", "climbing",
    "bouldering", "yoga", "dance", "dancing", "sing", "sings", "singing",
    "play", "plays", "playing", "game", "games", "board", "cards", "chess",
    "art", "arts", "paint", "painting", "draw", "drawing", "photo", "photos",
    "write", "writes", "writing", "science", "math", "code", "coding",
    "design", "creative", "nonfiction", "fiction", "poetry", "theatre",
    "theater", "improv", "comedy", "podcast", "podcasts", "language",
    "languages", "travel", "travels", "dog", "dogs", "cat", "cats", "kids",
    "children", "family", "eventually", "someday", "maybe", "probably",
    "actually", "really", "very", "pretty", "quite", "more", "most", "less",
    "much", "many", "few", "some", "any", "all", "every", "out", "up", "down",
    "go", "goes", "going", "went", "come", "comes", "get", "gets", "make",
    "makes", "take", "takes", "talk", "talks", "talking", "phone", "phones",
    "dinner", "lunch", "brunch", "weekend", "weekends", "weeknight", "night",
    "morning", "evening", "regular", "regulars", "competitive", "casual",
    "everywhere", "outside", "inside", "home", "city", "town", "local",
    "there", "here", "their", "them", "they", "she", "he", "her", "him",
    "his", "hers", "i", "me", "my", "mine", "we", "us", "our", "you", "your",
    "it", "its", "also", "too", "just", "still", "own", "new", "own",
    # Frequent enough that treating one as a name is a false positive, and a
    # gate that flags honest input teaches the user to skim the output.
    "rather", "though", "although", "always", "never", "often", "sometimes",
    "usually", "enough", "better", "best", "worse", "first", "last", "next",
    "other", "another", "together", "alone", "around", "through", "after",
    "before", "since", "while", "during", "again", "ever", "everything",
    "something", "nothing", "anything", "thing", "things", "stuff", "lot",
    "bit", "way", "ways", "time", "times", "day", "days", "week", "weeks",
    "month", "months", "place", "places", "room", "rooms", "world", "life",
    "part", "type", "side", "end", "start", "begin", "keep", "keeps", "stay",
    "stays", "find", "finds", "look", "looks", "feel", "feels", "think",
    "thinks", "know", "knows", "need", "needs", "try", "tries", "help",
    "helps", "meet", "meets", "meeting", "spend", "spends", "share", "shares",
    "build", "builds", "learn", "learns", "teach", "teaches", "listen",
    "listens", "watch", "watches", "shows", "show", "joke", "jokes", "laugh",
    "laughs", "care", "cares", "honest", "honestly", "direct", "ambitious",
    "driven", "thoughtful", "generous", "independent", "adventurous",
    "outdoorsy", "introvert", "extrovert", "nerdy", "geeky", "sarcastic",
    "witty", "dry", "humour", "humor", "sense", "values", "marriage",
    "married", "single", "relationship", "dating", "date", "dates", "please",
    "thanks", "hello", "sorry", "maybe", "okay", "fine", "fun", "happy",
    "tired", "busy", "free", "late", "early", "close", "near", "far", "away",
    "back", "front", "left", "right", "high", "low", "big", "small", "little",
)

# Protected characteristics. A venue row carrying one of these fails, whatever
# column it sits in and however much real justification is stacked beside it.
PROTECTED_TERMS = (
    "white", "black", "asian", "latina", "latino", "latinx", "hispanic",
    "arab", "desi", "indian", "chinese", "korean", "japanese", "filipino",
    "african", "european", "caucasian", "ethnic", "ethnicity", "race",
    "racial", "mixed-race", "jewish", "muslim", "christian", "catholic",
    "hindu", "buddhist", "sikh", "atheist", "religion", "religious",
    "immigrant", "expat", "nationality", "citizenship", "visa", "disabled",
    "disability", "neurodivergent", "autistic", "adhd", "bipolar",
    "depressed", "depression", "anxiety", "medicated", "psychiatric",
    "diagnosis", "diagnosed", "therapy", "sober", "recovering", "gay",
    "lesbian", "bisexual", "queer", "trans", "transgender", "straight",
    "orientation", "pregnant", "infertile", "virgin", "hot", "attractive",
    "pretty", "beautiful", "cute", "thin", "skinny", "fat", "overweight",
    "tall", "short", "blonde", "brunette", "redhead", "fit", "body",
)

# Anything that could put bytes on a wire. The skill drafts; the human sends.
SEND_MODULES = (
    "smtplib", "requests", "httpx", "aiohttp", "urllib.request", "urllib3",
    "http.client", "socket", "ftplib", "telnetlib", "paramiko", "selenium",
    "playwright", "twilio", "sendgrid", "boto3", "webbrowser", "imaplib",
    "poplib", "xmlrpc.client",
)

SEND_CALLS = (
    "sendmail", "send_message", "urlopen", "urlretrieve", "post", "put",
    "patch", "delete", "connect", "sendall", "send", "curl", "wget",
)

# Answers that look filled in and are not.
FILLER_ANSWERS = (
    "", "-", "--", "n/a", "na", "none", "idk", "i dont know", "i don't know",
    "dunno", "tbd", "todo", "?", "??", "...", "x", "xx", "whatever",
    "anything", "not sure", "unsure", "no idea", "same", "see above",
)

# Placeholder tokens. A block holding one of these must not be typed anywhere.
PLACEHOLDERS = (
    "REPLACE_ME", "TODO", "TBD", "FIXME", "XXX", "<name>", "<city>", "<place>",
    "[insert", "lorem ipsum", "PLACEHOLDER", "{{", "}}",
)

DENYLISTS: dict[str, tuple[str, ...]] = {
    "person_cues": PERSON_CUES,
    "institutions": INSTITUTIONS,
    "scene_nouns": SCENE_NOUNS,
    "common_words": COMMON_WORDS,
    "protected_terms": PROTECTED_TERMS,
    "send_modules": SEND_MODULES,
    "send_calls": SEND_CALLS,
    "filler_answers": FILLER_ANSWERS,
    "placeholders": PLACEHOLDERS,
}

MIN_LIST_SIZE = 8  # a list trimmed below this is a list someone gutted


def check_denylists() -> list[Finding]:
    """Fail closed. An empty required list is the defect, not a clean run."""
    out = []
    for name, items in DENYLISTS.items():
        live = [i for i in items if str(i).strip()]
        if len(live) < MIN_LIST_SIZE:
            out.append(Finding(
                "fail-closed", "empty-denylist",
                f"denylist {name!r} holds {len(live)} usable entries, under the floor of {MIN_LIST_SIZE}",
                "A preflight with an empty list passes every input and prints a green line.",
            ))
    return out


# --------------------------------------------------------------------------
# Guard 1 — the seed is a type, not a person.
# --------------------------------------------------------------------------

EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[a-z]{2,}\b", re.I)
PHONE = re.compile(r"(?<!\d)(?:\+?\d{1,2}[ .-]?)?\(?\d{3}\)?[ .-]\d{3}[ .-]\d{4}(?!\d)")
HANDLE = re.compile(r"(?<![\w.@])@[A-Za-z][\w.]{1,29}\b")
PROFILE_URL = re.compile(
    r"\b(?:https?://)?(?:www\.)?"
    r"(instagram|ig|facebook|fb|linkedin|twitter|x|tiktok|snapchat|hinge|bumble|"
    r"tinder|reddit|strava|spotify|venmo|discord)\.(?:com|co|me|gg)/\S+", re.I)
# "the one in my Tuesday class", "my 9am lab" — one slot on one timetable.
SINGULAR_SLOT = re.compile(
    r"\b(?:my|the|her|his)\s+"
    r"(?:\d{1,2}(?::\d{2})?\s*(?:am|pm)\s+|"
    r"(?:mon|tues|wednes|thurs|fri|satur|sun)day\s+|"
    r"(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\s+)?"
    r"(?:class|lab|section|seminar|lecture|tutorial|shift|office|dorm|floor|building)\b",
    re.I)
STREET = re.compile(r"\b(?:on|at)\s+(?:the\s+)?\d{0,5}\s*[A-Z][a-z]+\s+"
                    r"(?:st|street|ave|avenue|rd|road|blvd|way|drive|dr|lane|ln)\b", re.I)

DAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")


def _words(text: str) -> list[str]:
    return re.findall(r"[A-Za-z][A-Za-z'-]*", text)


def _name_shaped(token: str) -> bool:
    """A token that is not seed vocabulary, not a scene noun, not a weekday."""
    low = token.lower().strip("'-")
    if len(low) < 2:
        return False
    if low in COMMON_WORDS or low in SCENE_NOUNS or low in DAYS:
        return False
    if low in INSTITUTIONS or low in PROTECTED_TERMS:
        return False
    return True


def check_seed(text: str) -> list[Finding]:
    """Refuse a seed that resolves to one person.

    Everything downstream is a location-intelligence pipeline. Pointed at a
    category it is planning. Pointed at one person it is stalking, and the only
    difference is text you would otherwise accept as freeform.
    """
    why = ("A seed naming an individual turns venue lookup, organiser "
           "calendars, recurrence and travel time into surveillance of one "
           "person. Describe the type. Delete the person.")
    out: list[Finding] = []
    # Newlines are not a hiding place: a name split across two lines is a name.
    flat = " ".join(text.split())
    low = flat.lower()
    mixed_case = flat != low and flat != flat.upper()

    if hit := EMAIL.search(flat):
        out.append(Finding("seed", "contact-email", f"the seed holds an email address: {hit.group(0)}", why))
    if hit := PHONE.search(flat):
        out.append(Finding("seed", "contact-phone", f"the seed holds a phone number: {hit.group(0)}", why))
    if hit := PROFILE_URL.search(flat):
        out.append(Finding("seed", "profile-url", f"the seed holds a profile link: {hit.group(0)}", why))
    elif hit := HANDLE.search(flat):
        out.append(Finding("seed", "handle", f"the seed holds an account handle: {hit.group(0)}", why))
    for cue in PERSON_CUES:
        if cue in low:
            out.append(Finding("seed", "person-cue", f"the seed points at one person: {cue!r}", why))
            break
    if hit := SINGULAR_SLOT.search(flat):
        out.append(Finding("seed", "singular-slot", f"the seed names one timetable slot: {hit.group(0).strip()!r}", why))
    if hit := STREET.search(flat):
        out.append(Finding("seed", "street-address", f"the seed names one address: {hit.group(0).strip()!r}", why))

    # A name bound to a place. Case is irrelevant, so ALL CAPS, all lowercase
    # and MiXeD all land in the same place.
    name_bind = re.compile(
        r"\b([A-Za-z][\w'-]+)(?:\s+([A-Za-z][\w'-]+))?\s*(?:,|\bat\b|\bfrom\b|\bworks at\b|@)\s+"
        r"(?:the\s+)?([A-Za-z][\w'-]+)", re.I)
    for m in name_bind.finditer(flat):
        first, second, place = m.group(1), m.group(2), m.group(3)
        ident = [t for t in (first, second) if t and _name_shaped(t)]
        # "Jane Doe" and "JANE DOE" and "jane doe" all count. "venue lookup"
        # in a mixed-case sentence does not.
        if mixed_case and ident and not ident[0][:1].isupper():
            continue
        # One loose token is a hobby word. Two adjacent is a name.
        full_name = len(ident) == 2
        # A single name-shaped token still counts when a person cue is nearby.
        if not full_name:
            continue
        place_low = place.lower()
        located = place_low in INSTITUTIONS or _name_shaped(place)
        if located:
            out.append(Finding(
                "seed", "name-institution",
                f"the seed binds a name to a place: {' '.join(ident)} + {place}",
                why))
            break

    # A single capitalised given name bound to one definite room: "Sarah from
    # the coffee shop". Case matters here, which is why it is a separate rule
    # from the one above — that one has to ignore case to catch ALL CAPS.
    if not any(f.rule == "name-institution" for f in out):
        cap_bind = re.compile(
            r"\b([A-Z][a-z][\w'-]*)\s+(?:,\s*|at\s+|from\s+|works at\s+|who works at\s+)"
            r"(?:the\s+|my\s+)([A-Za-z][\w'-]+)(?:\s+([A-Za-z][\w'-]+))?")
        for m in cap_bind.finditer(flat):
            name, head, tail = m.group(1), m.group(2), m.group(3)
            if not _name_shaped(name):
                continue
            # Activity nouns in a seed are gerunds or plurals — "Bouldering at
            # the gym", "Ceramics at the studio". Given names are neither.
            if name.lower().endswith(("ing", "s")):
                continue
            # "Music Society", "Board Games Club" — a capitalised scene is a room.
            following = (head or "", tail or "")
            if any(w.lower() in SCENE_NOUNS for w in (name,)):
                continue
            room_word = any(w.lower() in SCENE_NOUNS or w.lower() in INSTITUTIONS for w in following)
            if room_word or _name_shaped(head):
                out.append(Finding(
                    "seed", "name-place",
                    f"the seed binds a name to one room: {name} + {' '.join(w for w in following if w)}",
                    why))
                break
    return out


# --------------------------------------------------------------------------
# Guard 2 — adult age floor, machine-readable, agreeing in two files.
# --------------------------------------------------------------------------

AGE_IN_TEXT = re.compile(r"^\s*age[_ -]?floor\s*[:=]\s*(\d{1,3})\s*$", re.I | re.M)
LEGAL_FLOOR = 18


def check_age_floor(config: dict, plan_text: str) -> list[Finding]:
    why = ("The seed is freeform and nothing else in the pipeline constrains "
           "it. The floor must be a number a script can read, in both files, "
           "and the two must agree.")
    out: list[Finding] = []
    cfg = config.get("age_floor")
    if cfg is None:
        out.append(Finding("age", "missing-config", "planrc.json has no `age_floor`", why))
    elif not isinstance(cfg, int):
        out.append(Finding("age", "unreadable", f"planrc.json `age_floor` is {cfg!r}, not an integer", why))
    elif cfg < LEGAL_FLOOR:
        out.append(Finding("age", "below-floor", f"planrc.json `age_floor` is {cfg}, under {LEGAL_FLOOR}", why))

    hit = AGE_IN_TEXT.search(plan_text)
    if hit is None:
        out.append(Finding("age", "missing-plan", "the plan has no `age_floor: NN` line", why))
    else:
        plan_floor = int(hit.group(1))
        if plan_floor < LEGAL_FLOOR:
            out.append(Finding("age", "below-floor", f"the plan states `age_floor: {plan_floor}`, under {LEGAL_FLOOR}", why))
        elif isinstance(cfg, int) and plan_floor != cfg:
            out.append(Finding("age", "disagree", f"planrc.json says {cfg}, the plan says {plan_floor}", why))
    return out


# --------------------------------------------------------------------------
# Guard 3 — no protected characteristic as a search axis.
# --------------------------------------------------------------------------

def check_room_rows(rows: Iterable[dict]) -> list[Finding]:
    """A row is refused if a protected term appears in any of its cells.

    Moving the word to another column does not help. Padding it with a real
    clause does not help. The justification language is the tell, because that
    is the language that leaks into how the user talks about it.
    """
    why = ("A venue you cannot justify without naming the category is "
           "targeting, not taste. Rewrite the reason so it still holds with "
           "the word deleted, or drop the row.")
    out: list[Finding] = []
    for row in rows:
        label = row.get("room") or row.get("Room") or "<unnamed row>"
        for column, cell in row.items():
            for word in re.findall(r"[A-Za-z][\w'-]*", str(cell)):
                if word.lower() in PROTECTED_TERMS:
                    out.append(Finding(
                        "rooms", "protected-axis",
                        f"row {label!r}, column {column!r} names a protected characteristic: {word!r}",
                        why))
    return out


# --------------------------------------------------------------------------
# Guard 4 — no send path.
# --------------------------------------------------------------------------

def check_no_send_path(paths: Iterable[Path]) -> list[Finding]:
    """Read every script as a syntax tree. Imports hide in strings; nodes do not."""
    why = ("The skill drafts. The human sends, types, and walks in. No "
           "autonomous sending, no scraping, no bulk action, no driving an "
           "account whose terms forbid scripted access.")
    out: list[Finding] = []
    for path in sorted(paths):
        if path.suffix != ".py":
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as err:
            out.append(Finding("send", "unparsable", f"{path.name} does not parse ({err})", why))
            continue
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            for name in names:
                root = name.split(".")[0]
                if name in SEND_MODULES or root in {m.split(".")[0] for m in SEND_MODULES}:
                    out.append(Finding("send", "network-import",
                                       f"{path.name} line {node.lineno} imports {name!r}", why))
            if isinstance(node, ast.Call):
                func = node.func
                label = getattr(func, "attr", None) or getattr(func, "id", None)
                if label in ("urlopen", "sendmail", "urlretrieve", "sendall"):
                    out.append(Finding("send", "network-call",
                                       f"{path.name} line {node.lineno} calls {label}()", why))
    return out


# --------------------------------------------------------------------------
# Guard 5 — fail closed on a table whose columns were renamed.
# --------------------------------------------------------------------------

def parse_table(text: str, heading: str, required: Iterable[str]) -> list[dict]:
    """Return the rows under `heading`, or raise. Never return an empty list quietly.

    A renamed column is a schema change, and a schema change must stop the run
    rather than print a card with blank fields.
    """
    required = list(required)
    lines = text.split("\n")
    want = heading.lstrip("#").strip().lower()
    start = next((i for i, l in enumerate(lines)
                  if l.strip().startswith("#") and l.strip().lstrip("#").strip().lower() == want), None)
    if start is None:
        raise ValueError(
            f"no section headed {heading!r}. The parser keys on that heading, so "
            f"renaming it silently empties the table. Restore the heading or update the parser.")
    header = next((i for i in range(start + 1, len(lines)) if lines[i].lstrip().startswith("|")), None)
    if header is None:
        raise ValueError(f"section {heading!r} holds no table. Add one with columns: {', '.join(required)}.")
    cols = [c.strip().lower() for c in lines[header].strip().strip("|").split("|")]
    missing = [c for c in required if c.lower() not in cols]
    if missing:
        raise ValueError(
            f"table under {heading!r} is missing column(s): {', '.join(missing)}. "
            f"Found: {', '.join(cols)}. Rename them back, or change `required` here and "
            f"in every reader, in the same commit.")
    rows = []
    for line in lines[header + 2:]:
        if not line.strip().startswith("|"):
            break
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != len(cols):
            raise ValueError(
                f"a row under {heading!r} has {len(cells)} cells for {len(cols)} columns: {line.strip()!r}. "
                f"A dropped header column shifts every value one place left.")
        row = dict(zip(cols, cells))
        if any(v for v in row.values()):
            rows.append(row)
    if not rows:
        raise ValueError(f"table under {heading!r} has a header and no rows. Fill it in.")
    return rows


def load_config(path: Path) -> dict:
    """Read planrc.json, or fail with the field names the user has to set."""
    if not path.is_file():
        raise ValueError(
            f"{path.name} is missing. Copy templates/planrc.json and set `place` and `tz`. "
            f"Neither is inferred from the machine clock — that mistake once built an "
            f"entire calendar for a city 2,000 miles away.")
    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as err:
        raise ValueError(f"{path.name} is not valid JSON ({err}).") from err
    unset = [k for k in ("place", "tz") if not str(config.get(k, "")).strip()
             or str(config.get(k)).upper().startswith("REPLACE")]
    if unset:
        raise ValueError(
            f"{path.name}: {' and '.join('`' + k + '`' for k in unset)} "
            f"{'is' if len(unset) == 1 else 'are'} unset. Ask the user and restate the answer. "
            f"Do not read it off the system clock.")
    return config


if __name__ == "__main__":  # a bare run reports what is loaded
    for name, items in DENYLISTS.items():
        print(f"{name:16} {len(items):4} entries")
    problems = check_denylists()
    print("denylists: " + ("ok" if not problems else "\n".join(str(p) for p in problems)))
