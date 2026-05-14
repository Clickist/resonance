# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project purpose

A Claude Code skill that analyzes an Apple Music library and generates a personalized HTML report with playlist recommendations. The analysis is driven entirely by metadata (no BPM — all zero in this library) and behavioral signals (play count, skip count, date patterns).

## Directory structure

```
├── extract_library.js      # JXA extraction script
├── extract_library.sh      # shell wrapper (runs extract_library.js)
├── analyze_library.py      # analysis script
├── run_analysis.sh         # full pipeline (extract + analyze)
├── artist_countries.json   # manually maintained artist→country lookup
├── data/
│   ├── library.json        # generated: raw Apple Music export
│   └── analysis.json       # generated: analysis output
├── docs/
│   └── content_spec.md     # finalized HTML content spec
└── claude_design/          # design system reference (DESIGN.md)
```

## Data extraction

```bash
./extract_library.sh          # re-extract Apple Music library → library.json
osascript -l JavaScript extract_library.js  # same, direct
```

`extract_library.js` is a JXA (JavaScript for Automation) script targeting `application("Music").libraryPlaylists[0]`. The output `library.json` is a flat array of track objects. Key fields and their reliability:

| Field | Coverage | Notes |
|---|---|---|
| name / artist / album / genre | ~100% | |
| playCount / lastPlayed | 86% | Main behavioral signal |
| skipCount | 44% | Unreliable — do not use for preference analysis |
| dateAdded | ~100% | Drives timeline analysis |
| loved / rating | 0% | User doesn't use these features |
| bpm | 0% | Not populated; skip entirely |

## Analysis dimensions (agreed)

1. **执念指数** — top tracks/artists by play count
3. **遗忘架** — added >X years ago, never or barely played
4. **趣味时间线** — genre distribution bucketed by dateAdded month
5. **爆发期识别** — periods of dense adds (discovery bursts)
7. **文化倾向推断** — Claude narrative: J-Pop+Anime ≈27%, Pop/Alternative split, no explicit curation behaviour

Do **not** build: skip-based preference analysis (skipCount unreliable), loved/rating dimensions.

## HTML output

Target format: **narrative scroll page** — long-form editorial with chapter sections, each pairing a Claude-written text interpretation with a supporting chart. Design reference is in `claude_design/DESIGN.md` (warm cream canvas, coral accents, serif display headlines, dark navy code surfaces). The page must also support interactive playlist confirmation (user reviews recommended tracks → confirms → outputs AppleScript to create playlist in Apple Music).

## Playlist creation

After analysis, generate an AppleScript (via `osascript`) that creates a new playlist in Apple Music and adds tracks to it. Always show the track list to the user for confirmation before executing.

Template:
```applescript
tell application "Music"
  set newPlaylist to make new playlist with properties {name: "..."}
  -- add tracks by persistent ID or search by name+artist
end tell
```
