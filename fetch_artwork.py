#!/usr/bin/env python3
"""
Fetch album artwork URLs from the iTunes Search API for a list of
(artist, track) pairs and write a flat JSON map to data/artwork.json.

The map key is "<artist>|<name>" (exactly as it appears in the
report.html inline DATA), and the value is a CDN URL upsized to 600x600.
Missing matches are written as null so the renderer can fall back.

Source list is hardcoded below — currently the S2 top tracks (10) and
S4 ghost tracks (8) that the report curates. Re-run when you add new
entries; the script de-dupes and skips keys already present in
data/artwork.json unless --refresh is passed.

Usage:
  python3 fetch_artwork.py            # incremental
  python3 fetch_artwork.py --refresh  # re-fetch every entry
"""

from __future__ import annotations

import argparse
import html
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "data" / "artwork.json"

# Curated lists from report.html inline DATA (kept in sync manually).
S2_TOP_TRACKS = [
    ("Harry Styles", "Golden"),
    ("Harry Styles", "Watermelon Sugar"),
    ("Harry Styles", "Adore You"),
    ("Queen", "Under Pressure (feat. David Bowie)"),
    ("Queen", "I Want To Break Free"),
    ("Harry Styles", "Lights Up"),
    ("milet, Aimer & Lilas Ikuta", "おもかげ (produced by Vaundy)"),
    ("Sia Furler", "Snowman"),
    ("Eiichi Otaki", "Velvet Motel"),
    ("Eiichi Otaki", "カナリア諸島にて"),
]

S4_GHOST_TRACKS = [
    ("放課後ティータイム", "放課後ティータイム"),
    ("放課後ティータイム", "ふわふわ時間 (#23 Mix)"),
    ("放課後ティータイム", "カレーのちライス"),
    ("LiSA", "My Soul, Your Beats!"),
    ("Linked Horizon", "紅蓮の弓矢"),
    ("μ’s", "Snow halation"),
    ("放課後ティータイム", "Don’t say lazy"),
    ("放課後ティータイム", "Cagayake! GIRLS"),
]

# S1 hero now-card track (most recently added).
S1_NOW_CARD = [
    ("Mac DeMarco", "Chamber of Reflection"),
]

# S7 — three playlists. Forgotten Awakening / Recent Vein rebuilt in
# 2026-05 after audit: previous values had ~8 fabricated tracks that
# didn't exist in library.json. New lists are ground-truthed against
# analysis.json (forgotten side) and iTunes Search verification
# (recent side, since those are recommendations of new music).

# Forgotten Awakening — pulled from analysis.json.forgottenShelf,
# diversified by genre to avoid stacking K-On entries (which already
# dominate the S4 ghost list).
S7_FORGOTTEN_AWAKENING = [
    ("星野源", "Koi"),
    ("majiko", "心做し"),
    ("Aimer", "悲しみの向こう側"),
    ("Eve", "Kaikai Kitan"),
    ("Simon & Garfunkel", "The Sound of Silence"),
    ("Mariah Carey", "Oh Santa! (feat. Ariana Grande & Jennifer Hudson)"),
    ("Adele", "Hello"),
    ("μ’s", "もぎゅっと\"love\"で接近中!"),
]

# Recent Vein — these are *recommendations*, not library tracks.
# Each entry has been verified against iTunes Search (artist + track
# soft-match) AND cross-checked NOT to be in library.json. The
# verification gate lives in verify_candidates.py.
S7_RECENT_VEIN = [
    ("Shing02", "400 (Vocal)"),
    ("haruka nakamura", "lamp"),
    ("Bonobo", "Kerala"),
    ("Tycho", "Awake"),
    ("Suchmos", "Stay Tune"),
    ("Connan Mockasin", "Forever Dolphin Love"),
    ("Steve Lacy", "Dark Red"),
    ("Khruangbin", "Maria También"),
]

S7_OBSESSION_REPLAY = [
    # Overlaps entirely with S2_TOP_TRACKS — dedup at run time.
    *S2_TOP_TRACKS,
]

ITUNES_ENDPOINT = "https://itunes.apple.com/search"
USER_AGENT = "music-analyzer-skill/1.0 (artwork prefetch)"
THROTTLE_SECONDS = 0.4  # ~150/min — well under iTunes' soft limit


def make_key(artist: str, name: str) -> str:
    return f"{artist}|{name}"


def clean_term(s: str) -> str:
    # iTunes search treats most punctuation as a separator; strip
    # parenthetical qualifiers + smart quotes for a cleaner match.
    s = html.unescape(s)
    s = s.replace("’", "'").replace("‘", "'")
    # Drop trailing parenthetical hints — they often contain "feat.",
    # mix names, or producer credits that hurt matching.
    if "(" in s:
        s = s.split("(", 1)[0].strip()
    return s


def fetch_one(artist: str, name: str) -> str | None:
    term = f"{clean_term(artist)} {clean_term(name)}"
    params = urllib.parse.urlencode(
        {"term": term, "entity": "song", "limit": 1, "media": "music"}
    )
    url = f"{ITUNES_ENDPOINT}?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  ! fetch failed for {artist} / {name}: {e}", file=sys.stderr)
        return None
    results = payload.get("results") or []
    if not results:
        return None
    art = results[0].get("artworkUrl100")
    if not art:
        return None
    # Upsize: replace the trailing "/100x100bb.jpg" with "/600x600bb.jpg".
    return art.replace("100x100bb", "600x600bb")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Re-fetch every entry, ignoring existing data/artwork.json",
    )
    args = parser.parse_args()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    existing: dict[str, str | None] = {}
    if OUT.exists() and not args.refresh:
        existing = json.loads(OUT.read_text("utf-8"))

    all_entries = (
        S2_TOP_TRACKS
        + S4_GHOST_TRACKS
        + S1_NOW_CARD
        + S7_FORGOTTEN_AWAKENING
        + S7_RECENT_VEIN
        + S7_OBSESSION_REPLAY
    )
    seen: set[str] = set()
    result: dict[str, str | None] = dict(existing)

    new_calls = 0
    for artist, name in all_entries:
        key = make_key(artist, name)
        if key in seen:
            continue
        seen.add(key)
        if key in result and result[key] is not None and not args.refresh:
            print(f"  - skip (cached): {key}")
            continue
        print(f"  · fetch: {key}")
        result[key] = fetch_one(artist, name)
        new_calls += 1
        time.sleep(THROTTLE_SECONDS)

    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), "utf-8")
    hits = sum(1 for v in result.values() if v)
    print(
        f"\nDone. {hits}/{len(result)} entries have artwork. "
        f"New API calls this run: {new_calls}. Wrote {OUT.relative_to(ROOT)}."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
