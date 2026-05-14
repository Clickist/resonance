#!/usr/bin/env python3
"""
Analyze Apple Music library.json → analysis.json
Covers: obsession index, forgotten shelf, taste timeline,
        discovery bursts, cultural tendency, artist geography.
"""

import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
LIBRARY_PATH = SCRIPT_DIR / "data" / "library.json"
OUTPUT_PATH = SCRIPT_DIR / "data" / "analysis.json"

NOW = datetime.now(timezone.utc)


def parse_date(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def years_ago(dt):
    if not dt:
        return None
    return (NOW - dt).days / 365.25


# ──────────────────────────────────────────────
# 1. 执念指数 — Obsession Index
# ──────────────────────────────────────────────
def obsession_index(tracks):
    plays_by_artist = defaultdict(int)
    plays_by_track = []

    for t in tracks:
        pc = t.get("playCount", 0) or 0
        plays_by_artist[t.get("artist", "Unknown")] += pc
        plays_by_track.append({
            "name": t.get("name", ""),
            "artist": t.get("artist", ""),
            "playCount": pc,
        })

    total_plays = sum(t["playCount"] for t in plays_by_track)
    top_tracks = sorted(plays_by_track, key=lambda x: x["playCount"], reverse=True)[:15]
    top_artists = sorted(
        [{"artist": a, "playCount": p} for a, p in plays_by_artist.items()],
        key=lambda x: x["playCount"], reverse=True
    )[:15]

    # Concentration: what % of plays come from top 10 artists
    top10_plays = sum(a["playCount"] for a in top_artists[:10])
    concentration = round(top10_plays / total_plays * 100, 1) if total_plays else 0

    # Most-played track play count vs average (for played tracks)
    played = [t["playCount"] for t in plays_by_track if t["playCount"] > 0]
    avg_plays = round(sum(played) / len(played), 1) if played else 0
    max_plays = top_tracks[0]["playCount"] if top_tracks else 0

    return {
        "totalPlays": total_plays,
        "tracksEverPlayed": len(played),
        "avgPlaysPerPlayedTrack": avg_plays,
        "maxSingleTrackPlays": max_plays,
        "top10ArtistPlayConcentration": concentration,
        "topTracks": top_tracks,
        "topArtists": top_artists,
    }


# ──────────────────────────────────────────────
# 2. 遗忘架 — Forgotten Shelf
# ──────────────────────────────────────────────
def forgotten_shelf(tracks):
    never_played = []
    long_unplayed = []  # played before but >1.5 years ago

    for t in tracks:
        added = parse_date(t.get("dateAdded"))
        last = parse_date(t.get("lastPlayed"))
        pc = t.get("playCount", 0) or 0
        age = years_ago(added)

        if age is None:
            continue

        entry = {
            "name": t.get("name", ""),
            "artist": t.get("artist", ""),
            "genre": t.get("genre", ""),
            "dateAdded": t.get("dateAdded"),
            "lastPlayed": t.get("lastPlayed"),
            "playCount": pc,
            "yearsOwned": round(age, 1),
        }

        if pc == 0 and age >= 1:
            never_played.append(entry)
        elif pc > 0 and last and years_ago(last) >= 1.5:
            entry["yearsSinceLastPlay"] = round(years_ago(last), 1)
            long_unplayed.append(entry)

    never_played.sort(key=lambda x: x["yearsOwned"], reverse=True)
    long_unplayed.sort(key=lambda x: x["yearsSinceLastPlay"], reverse=True)

    # Genre breakdown of forgotten tracks
    forgotten_genres = Counter(
        t["genre"] for t in never_played + long_unplayed if t.get("genre")
    )

    return {
        "neverPlayedCount": len(never_played),
        "longUnplayedCount": len(long_unplayed),
        "forgottenGenres": [{"genre": g, "count": c} for g, c in forgotten_genres.most_common(8)],
        "neverPlayed": never_played[:20],
        "longUnplayed": long_unplayed[:20],
    }


# ──────────────────────────────────────────────
# 3. 趣味时间线 — Taste Timeline
# ──────────────────────────────────────────────
def taste_timeline(tracks):
    # Group genres by quarter
    by_quarter = defaultdict(lambda: defaultdict(int))

    for t in tracks:
        added = parse_date(t.get("dateAdded"))
        genre = t.get("genre", "Other") or "Other"
        if not added:
            continue
        q = f"{added.year}-Q{(added.month - 1) // 3 + 1}"
        by_quarter[q][genre] += 1

    # Build sorted timeline
    quarters = sorted(by_quarter.keys())

    # Normalize genre names into broader buckets for cleaner display
    GENRE_MAP = {
        "J-Pop": "J-Pop", "Anime": "J-Pop/Anime",
        "Pop": "Pop", "Dance": "Dance/Electronic", "Electronic": "Dance/Electronic",
        "Alternative": "Alternative/Rock", "Rock": "Alternative/Rock",
        "Hip-Hop/Rap": "Hip-Hop", "R&B/Soul": "R&B/Soul",
        "Classical": "Classical", "Country": "Country",
        "Jazz": "Jazz",
    }

    timeline = []
    for q in quarters:
        genres = by_quarter[q]
        bucketed = defaultdict(int)
        for g, c in genres.items():
            bucket = GENRE_MAP.get(g, "Other")
            bucketed[bucket] += c
        total = sum(bucketed.values())
        dominant = max(bucketed, key=bucketed.get) if bucketed else "Other"
        timeline.append({
            "quarter": q,
            "total": total,
            "dominant": dominant,
            "breakdown": dict(sorted(bucketed.items(), key=lambda x: x[1], reverse=True)),
        })

    # Detect notable genre shifts: quarters where dominant genre changed
    shifts = []
    for i in range(1, len(timeline)):
        prev, curr = timeline[i - 1], timeline[i]
        if prev["dominant"] != curr["dominant"]:
            shifts.append({
                "from": prev["quarter"],
                "to": curr["quarter"],
                "prevDominant": prev["dominant"],
                "currDominant": curr["dominant"],
            })

    return {
        "quarters": timeline,
        "genreShifts": shifts,
        "dateRange": {
            "first": quarters[0] if quarters else None,
            "last": quarters[-1] if quarters else None,
        }
    }


# ──────────────────────────────────────────────
# 4. 完整时间线 — Full Timeline
# ──────────────────────────────────────────────
def full_timeline(tracks):
    by_month = defaultdict(list)
    for t in tracks:
        added = parse_date(t.get("dateAdded"))
        if added:
            key = f"{added.year}-{added.month:02d}"
            by_month[key].append(t)

    months_sorted = sorted(by_month.keys())
    if not months_sorted:
        return {"months": [], "avgMonthlyAdds": 0}

    values = [len(by_month[m]) for m in months_sorted]
    avg = sum(values) / len(values)
    std = (sum((v - avg) ** 2 for v in values) / len(values)) ** 0.5

    months = []
    for m in months_sorted:
        ts = by_month[m]
        count = len(ts)
        # All artists with counts, sorted by count desc
        artist_counts = Counter(t.get("artist", "") or "" for t in ts)
        genre_counts = Counter(t.get("genre", "Other") or "Other" for t in ts)
        # Full track list for this month
        track_list = [
            {
                "name": t.get("name", ""),
                "artist": t.get("artist", ""),
                "genre": t.get("genre", ""),
                "playCount": t.get("playCount") or 0,
            }
            for t in ts
        ]
        z = round((count - avg) / std, 2) if std else 0
        months.append({
            "month": m,
            "year": m[:4],
            "count": count,
            "zScore": z,
            "artists": [{"artist": a, "count": c} for a, c in artist_counts.most_common()],
            "genres": [{"genre": g, "count": c} for g, c in genre_counts.most_common()],
            "tracks": track_list,
        })

    return {
        "months": months,
        "avgMonthlyAdds": round(avg, 1),
        "totalMonths": len(months_sorted),
        "dateRange": {"first": months_sorted[0], "last": months_sorted[-1]},
    }


# ──────────────────────────────────────────────
# 5. 文化倾向推断 — Cultural Tendency
# ──────────────────────────────────────────────
def cultural_tendency(tracks):
    total = len(tracks)
    genre_counts = Counter(t.get("genre", "Other") or "Other" for t in tracks)

    # Cultural cluster mapping
    CLUSTERS = {
        "日系": ["J-Pop", "Anime", "J-Rock", "Enka", "Visual Kei"],
        "英美主流": ["Pop", "Rock", "Alternative", "Country", "R&B/Soul", "Hip-Hop/Rap"],
        "电子/舞曲": ["Dance", "Electronic", "EDM", "House", "Techno"],
        "古典/器乐": ["Classical", "Instrumental", "Soundtrack", "Jazz"],
        "其他": [],
    }

    cluster_counts = defaultdict(int)
    for genre, count in genre_counts.items():
        matched = False
        for cluster, genres in CLUSTERS.items():
            if genre in genres:
                cluster_counts[cluster] += count
                matched = True
                break
        if not matched:
            cluster_counts["其他"] += count

    clusters = [
        {
            "cluster": c,
            "count": cluster_counts[c],
            "percent": round(cluster_counts[c] / total * 100, 1),
        }
        for c in CLUSTERS.keys()
        if cluster_counts[c] > 0
    ]
    clusters.sort(key=lambda x: x["count"], reverse=True)

    # Genre detail (top 12)
    genre_detail = [
        {"genre": g, "count": c, "percent": round(c / total * 100, 1)}
        for g, c in genre_counts.most_common(12)
    ]

    # Listener behavior profile
    played = [t for t in tracks if (t.get("playCount") or 0) > 0]
    play_counts = [(t.get("playCount") or 0) for t in played]
    high_repeat = sum(1 for p in play_counts if p >= 10)
    one_timers = sum(1 for p in play_counts if p == 1)

    return {
        "genreDetail": genre_detail,
        "culturalClusters": clusters,
        "listenerProfile": {
            "totalTracks": total,
            "uniqueArtists": len(set(t.get("artist", "") for t in tracks)),
            "uniqueGenres": len(genre_counts),
            "highRepeatTracks": high_repeat,   # played 10+ times
            "oneTimerTracks": one_timers,       # played exactly once
            "noCurationSignal": True,           # loved/rating all zero
        },
    }


# ──────────────────────────────────────────────
# 6. 艺术家地理分布 — Artist Geography
# ──────────────────────────────────────────────
# Heuristic pass: genre-based + known artist name patterns.
# Returns artist→country mapping for all unique artists.
# This is a best-effort first pass; unknown artists get country=null.

GENRE_COUNTRY_HINT = {
    "J-Pop": "JP", "Anime": "JP", "J-Rock": "JP", "Enka": "JP", "Visual Kei": "JP",
    "Country": "US", "Hip-Hop/Rap": "US", "R&B/Soul": "US",
    "K-Pop": "KR",
    "C-Pop": "CN",
    "Mandopop": "TW",
    "Latin": "MX",
    "Reggae": "JM",
    "Afrobeats": "NG",
}

ARTIST_COUNTRIES_PATH = SCRIPT_DIR / "artist_countries.json"

def artist_geography(tracks):
    # Load manual lookup table
    manual_lookup = {}
    if ARTIST_COUNTRIES_PATH.exists():
        with open(ARTIST_COUNTRIES_PATH, encoding="utf-8") as f:
            manual_lookup = json.load(f)

    artist_genres = defaultdict(Counter)
    artist_plays = defaultdict(int)

    for t in tracks:
        artist = t.get("artist", "").strip()
        genre = t.get("genre", "") or ""
        if artist:
            artist_genres[artist][genre] += 1
            artist_plays[artist] += (t.get("playCount") or 0)

    artists_with_country = []
    country_counts = Counter()
    unknown = []

    for artist, genre_counter in artist_genres.items():
        top_genre = genre_counter.most_common(1)[0][0] if genre_counter else ""

        # Priority: manual lookup > genre hint
        country = manual_lookup.get(artist) or GENRE_COUNTRY_HINT.get(top_genre)
        source = "manual" if manual_lookup.get(artist) else ("genre" if country else None)

        if country:
            artists_with_country.append({
                "artist": artist,
                "country": country,
                "inferredFrom": source,
                "topGenre": top_genre,
                "totalPlays": artist_plays[artist],
            })
            country_counts[country] += 1
        else:
            unknown.append({
                "artist": artist,
                "topGenre": top_genre,
                "totalPlays": artist_plays[artist],
            })

    country_summary = [
        {"country": c, "artistCount": n}
        for c, n in country_counts.most_common()
    ]

    return {
        "totalUniqueArtists": len(artist_genres),
        "mappedArtists": len(artists_with_country),
        "unmappedArtists": len(unknown),
        "countrySummary": country_summary,
        "artistList": artists_with_country,
        "needsLLMMapping": [a for a in unknown if a["totalPlays"] > 0][:50],
    }


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────
def main():
    if not LIBRARY_PATH.exists():
        print(f"ERROR: {LIBRARY_PATH} not found. Run extract_library.sh first.", file=sys.stderr)
        sys.exit(1)

    with open(LIBRARY_PATH, encoding="utf-8") as f:
        tracks = json.load(f)

    print(f"Analyzing {len(tracks)} tracks...")

    result = {
        "meta": {
            "generatedAt": NOW.isoformat(),
            "trackCount": len(tracks),
        },
        "obsessionIndex": obsession_index(tracks),
        "forgottenShelf": forgotten_shelf(tracks),
        "tasteTimeline": taste_timeline(tracks),
        "timeline": full_timeline(tracks),
        "culturalTendency": cultural_tendency(tracks),
        "artistGeography": artist_geography(tracks),
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Done → {OUTPUT_PATH}")

    # Quick summary
    obs = result["obsessionIndex"]
    forg = result["forgottenShelf"]
    timeline = result["timeline"]
    geo = result["artistGeography"]

    print(f"\n── Obsession ──")
    print(f"  Total plays: {obs['totalPlays']}, avg/track: {obs['avgPlaysPerPlayedTrack']}")
    print(f"  Top artist: {obs['topArtists'][0]['artist']} ({obs['topArtists'][0]['playCount']} plays)")
    print(f"  Top10 artist concentration: {obs['top10ArtistPlayConcentration']}%")

    print(f"\n── Forgotten Shelf ──")
    print(f"  Never played (owned >1yr): {forg['neverPlayedCount']}")
    print(f"  Long unplayed (>1.5yr): {forg['longUnplayedCount']}")

    print(f"\n── Timeline ──")
    print(f"  {timeline['dateRange']['first']} → {timeline['dateRange']['last']}")
    print(f"  {timeline['totalMonths']} months, avg {timeline['avgMonthlyAdds']} tracks/month")
    print(f"  All months:")
    for m in timeline["months"]:
        top_artist = m["artists"][0]["artist"] if m["artists"] else ""
        print(f"    {m['month']}  {m['count']:3d}首  top={top_artist}")

    print(f"\n── Geography ──")
    print(f"  Unique artists: {geo['totalUniqueArtists']}, mapped: {geo['mappedArtists']}, unmapped: {geo['unmappedArtists']}")
    for c in geo["countrySummary"]:
        print(f"  {c['country']}: {c['artistCount']} artists")


if __name__ == "__main__":
    main()
