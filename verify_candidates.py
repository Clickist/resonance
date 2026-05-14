#!/usr/bin/env python3
"""
Verify a list of (artist, track) candidates against:
  1. iTunes Search API — must return a song result whose artist
     matches (soft-normalised) and whose track name matches softly.
  2. data/library.json — must NOT already be in user's library.

Only candidates that pass BOTH gates are eligible for the
Recent Vein recommendation playlist.

Output: prints a verdict per candidate + emits the survivors as JSON
to stdout (under "passed").

Usage:
  python3 verify_candidates.py
"""

from __future__ import annotations

import html
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LIB = json.loads((ROOT / "data" / "library.json").read_text("utf-8"))

# Build a normalised library index for the "already-owned" check.
def norm(s: str) -> str:
    if not s:
        return ""
    s = html.unescape(s).lower()
    s = re.sub(r"[\s\W_]+", "", s)
    return s

LIB_INDEX = {(norm(t.get("artist", "")), norm(t.get("name", ""))) for t in LIB}
LIB_ARTISTS = {norm(t.get("artist", "")) for t in LIB}


# Candidate pool for Recent Vein. Each tuple is (artist, track, why-tag).
# The vein has two strands per the section narrative:
#   - Nujabes downstream (lo-fi / Japanese hip-hop)
#   - Recent western coda (Mac DeMarco / SZA / Bieber adjacency)
CANDIDATES = [
    # ---- Nujabes-adjacent (frequent collaborators or scene-mates)
    ("Uyama Hiroto", "Free Stylin' Sailor", "Nujabes' main collaborator, solo work"),
    ("Uyama Hiroto", "A Forest of Pianos", "Nujabes' main collaborator, solo work"),
    ("Shing02", "400", "Nujabes' lead MC, solo album"),
    ("Fat Jon", "Lightweight Heavyweight", "Samurai Champloo co-producer"),
    ("Fat Jon", "Repetition Defeats the Purpose", "Samurai Champloo co-producer"),
    ("Force Of Nature", "Battlecry", "Samurai Champloo OST"),
    ("Tsutchie", "San Francisco", "Samurai Champloo OST"),
    ("Substantial", "Suspended Animation", "Nujabes vocalist solo"),
    ("Funky DL", "Going On a Journey", "Nujabes-era UK hip-hop"),
    ("Haruka Nakamura", "Lamp", "Japanese ambient / Nujabes-adjacent"),
    ("Cradle", "Aenema", "Japanese hip-hop / Nujabes-adjacent label-mate"),
    ("Cise Starr", "Reborn", "CYNE rapper, on Nujabes' Feather"),

    # ---- Expanded lo-fi / instrumental hip-hop pool (commercial catalogs)
    ("Bonobo", "Kerala", "Downtempo, Nujabes-adjacent emotional palette"),
    ("Bonobo", "Cirrus", "Downtempo instrumental"),
    ("Tycho", "A Walk", "Ambient electronic, chill lineage"),
    ("Tycho", "Awake", "Ambient electronic"),
    ("Emancipator", "Soon It Will Be Cold Enough", "Downtempo, Nujabes scene"),
    ("Nightmares On Wax", "Les Nuits", "UK trip-hop / chill"),
    ("Mocky", "Time to Go", "Producer's instrumental side"),
    ("tofubeats", "Don't Stop the Music", "Japanese producer"),
    ("Yogee New Waves", "Climax Night", "Japanese indie"),
    ("Cero", "Summer Soul", "Japanese indie soul"),
    ("Suchmos", "STAY TUNE", "Japanese funk/hip-hop adjacent"),
    ("Lamp", "ひろがる空に", "Japanese indie band — bossa lineage"),
    ("Mitski", "Nobody", "Japanese-American indie, melancholic"),

    # ---- Recent western coda
    ("Frank Ocean", "Sweet Life", "SZA-adjacent R&B introspection"),
    ("Frank Ocean", "Nights", "SZA-adjacent R&B introspection"),
    ("Connan Mockasin", "Forever Dolphin Love", "Mac DeMarco-adjacent slacker pop"),
    ("Whitney", "No Woman", "Mac DeMarco-adjacent indie"),
    ("Homeshake", "Khmlwugh", "Mac DeMarco-adjacent (his ex-bandmate)"),
    ("Crumb", "Locket", "Indie psych close to Mac DeMarco's lane"),
    ("Khruangbin", "Maria También", "Instrumental groove, broad appeal"),
    ("Steve Lacy", "Dark Red", "Bieber/SZA-adjacent modern R&B"),
    ("Daniel Caesar", "Best Part", "SZA-adjacent R&B"),
]


def soft_match(a: str, b: str) -> bool:
    """Normalised substring match — handles punctuation/case/space drift."""
    na, nb = norm(a), norm(b)
    if not na or not nb:
        return False
    # Allow either-direction containment (iTunes returns "Sweet Life"
    # while we asked for "Sweet Life"; sometimes the API returns
    # "Sweet Life (Remix)" for the same query).
    return na in nb or nb in na


def itunes_search(artist: str, track: str) -> dict | None:
    term = f"{artist} {track}"
    params = urllib.parse.urlencode(
        {"term": term, "entity": "song", "limit": 5, "media": "music"}
    )
    req = urllib.request.Request(
        f"https://itunes.apple.com/search?{params}",
        headers={"User-Agent": "music-analyzer-skill/1.0 verify"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  ! fetch failed: {e}", file=sys.stderr)
        return None
    for r in payload.get("results") or []:
        # Require both artist + track to soft-match.
        if soft_match(artist, r.get("artistName", "")) and soft_match(
            track, r.get("trackName", "")
        ):
            return r
    return None


def main() -> int:
    out_passed = []
    out_failed = []
    out_already_owned = []

    for artist, track, why in CANDIDATES:
        ak, tk = norm(artist), norm(track)
        if (ak, tk) in LIB_INDEX:
            print(f"  - ALREADY OWNED  | {artist} | {track}")
            out_already_owned.append({"artist": artist, "track": track})
            continue

        hit = itunes_search(artist, track)
        time.sleep(0.35)
        if not hit:
            print(f"  ✗ NOT ON iTUNES  | {artist} | {track}")
            out_failed.append({"artist": artist, "track": track, "why": why})
            continue

        artwork = hit.get("artworkUrl100", "").replace("100x100bb", "600x600bb") or None
        canonical_artist = hit.get("artistName")
        canonical_track = hit.get("trackName")
        canonical_album = hit.get("collectionName")
        print(
            f"  ✓ VERIFIED       | {canonical_artist} | {canonical_track}  [{canonical_album}]"
        )
        out_passed.append(
            {
                "artist": canonical_artist,
                "track": canonical_track,
                "album": canonical_album,
                "artwork": artwork,
                "why": why,
            }
        )

    print(
        f"\nverdict: {len(out_passed)} passed · {len(out_failed)} not-on-iTunes · "
        f"{len(out_already_owned)} already-owned"
    )
    out = {
        "passed": out_passed,
        "not_on_itunes": out_failed,
        "already_owned": out_already_owned,
    }
    (ROOT / "data" / "recent_vein_candidates.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), "utf-8"
    )
    print("Wrote data/recent_vein_candidates.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
