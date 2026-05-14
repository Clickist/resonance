# Resonance

> Your play count is a diary you never meant to publish.

**Resonance** turns your Apple Music library into a long-form editorial report — a single, self-contained HTML page with seven narrative sections that tell you who you've been listening to, what you've forgotten, where your taste comes from, and where it's headed next.

No stars. No hearts. Only the quiet arithmetic of how many times you came back to a song.

📖 [中文版本](README_CN.md)

---

## How it works

Resonance is a three-stage pipeline. Each stage can run independently — re-run extraction when your library changes, or jump straight to the report if you already have analysis data.

```
┌─────────────────────────┐      ┌─────────────────────────┐      ┌─────────────────────────┐
│  1. EXTRACT             │      │  2. ANALYZE             │      │  3. RENDER              │
│                         │  ──▶ │                         │  ──▶ │                         │
│  extract_library.js     │      │  analyze_library.py     │      │  (Claude + template)    │
│  JXA · Apple Music      │      │                         │      │                         │
│                         │      │  6 analytical           │      │  7 narrative sections   │
│  → data/library.json    │      │  dimensions             │      │  + interactive          │
│     raw track metadata  │      │                         │      │    playlist generation  │
│                         │      │  → data/analysis.json   │      │                         │
│                         │      │    derived insights     │      │  → report.html          │
│                         │      │    + raw aggregations   │      │    self-contained       │
└─────────────────────────┘      └─────────────────────────┘      └─────────────────────────┘
```

### Stage 1 — Extract

`extract_library.js` is a JXA (JavaScript for Automation) script that talks directly to the Apple Music app on macOS. It reads your library playlist and writes every track — name, artist, album, genre, play count, date added, last played — to `data/library.json`.

```bash
./extract_library.sh
# or: osascript -l JavaScript extract_library.js
```

### Stage 2 — Analyze

`analyze_library.py` reads `data/library.json` and derives six analytical dimensions:

| Dimension | What it finds |
|---|---|
| **Obsession Index** | Top artists and tracks by play count; repeat-listening concentration |
| **Forgotten Shelf** | Tracks owned >1 year but never played, or played once then abandoned |
| **Taste Timeline** | Genre distribution per quarter, genre-shift events |
| **Discovery Bursts** | Months where you added unusually many tracks (z-score spikes) |
| **Cultural Tendency** | Genre → cultural cluster mapping, repeat vs. one-time listening ratio |
| **Artist Geography** | Artist → country mapping (manual lookup + genre heuristics) |

```bash
python3 analyze_library.py
# → data/analysis.json
```

### Stage 3 — Render

This is where Claude (the AI agent) does the creative heavy lifting. Given `analysis.json`, Claude:

1. **Curates** the inline DATA block — selects which tracks appear in each section, orders the timeline highlights, picks the Recent Vein recommendations
2. **Writes** editorial commentary — the narrative paragraphs that interpret what the numbers mean
3. **Fetches** album artwork via iTunes Search API (`fetch_artwork.py`)
4. **Fills** the `report.example.html` template with your data, producing `report.html`

The result is a single HTML file — no build step, no server, no framework. Open it in any browser, or double-click to read.

```bash
# After Claude generates your report:
open report.html
```

The rendered report contains **7 narrative sections**:

| Section | What you see |
|---|---|
| **Hero** | The most recently added track, plus library stats at a glance |
| **Obsession Archive** | Top 10 artists / top 10 tracks with album cover art and editorial commentary |
| **Timeline** | Sticky-scroll axis through every month you added music, 2020–present |
| **Forgotten Shelf** | The tracks you brought home and never opened — rendered as a ghostly album gallery |
| **Geography** | An interactive 3D globe showing where your artists come from, with per-country narrative cards |
| **Portrait** | Three trait cards distilling your listening personality |
| **Playlists** | Three generated playlists: Forgotten Awakening (unplayed gems from your library), Recent Vein (new music recommendations verified on Apple Music), and Obsession Replay (your 10 most-replayed tracks) — each with an AppleScript generator |

---

## Prerequisites

- macOS (the extraction stage uses JXA, which is macOS-only)
- Apple Music app with a local library
- Python 3.9+
- That's it. The rendered report requires only a browser.

---

## Quick start

```bash
# 1. Clone
git clone https://github.com/Clickist/resonance.git
cd resonance

# 2. Extract your Apple Music library
./extract_library.sh
# → data/library.json

# 3. Analyze
python3 analyze_library.py
# → data/analysis.json

# 4. Generate your report
#    Invoke Claude Code and say:
#    "Fill report.example.html with my analysis.json data.
#     Run fetch_artwork.py first for album covers.
#     Write editorial commentary for all sections.
#     Output as report.html."

# 5. Open
open report.html
```

Or, if you have [Claude Code](https://claude.ai/code) installed, install the skill and let Claude run the entire pipeline:

```bash
claude
# > Install the Resonance skill
# > /resonance
```

Claude will extract, analyze, curate, and produce your personalized `report.html`.

---

## File structure

```
resonance/
├── extract_library.js           # JXA: Apple Music → JSON
├── extract_library.sh           # Shell wrapper for extract_library.js
├── analyze_library.py           # Python analysis engine
├── fetch_artwork.py             # iTunes Search → album cover URLs
├── verify_candidates.py         # Gate: recommended tracks must exist on iTunes
├── artist_countries.json        # Manual artist → country lookup table
│
├── report.example.html          # Template (data scrubbed — your starting point)
├── report.html                  # Your generated report (gitignored)
│
├── data/
│   ├── library.json             # Raw Apple Music extract (gitignored)
│   ├── analysis.json            # Analysis output (gitignored)
│   └── artwork.json             # iTunes CDN URLs cache (no personal data)
│
├── .gitignore
├── README.md                    # You are here
└── README_CN.md                 # 中文版本
```

---

## Display features

- **Light / dark themes** — follows `prefers-color-scheme`; toggle button in the top nav overrides per session
- **3D globe** — interactive globe.gl visualization with auto-rotation; pauses when offscreen to save GPU
- **Album cover art** — fetched from iTunes CDN, displayed in Obsession Archive, Forgotten Shelf, and Playlists; Recent Vein recommendation covers link directly to Apple Music
- **Sticky timeline** — IntersectionObserver-driven year axis tracks your scroll position
- **AppleScript playlist generator** — review and edit any playlist, then generate a ready-to-run AppleScript that creates it in Apple Music
- **Single file** — `report.html` is fully self-contained; no build step, no bundler, no `node_modules`
- **Desktop-respecting performance** — globe render loop pauses when scrolled out of view; top-nav backdrop-filter drops past the hero

---

## Data privacy

- All extraction and analysis happens **locally on your machine**
- The inline `<script id="DATA">` JSON block contains your aggregated listening statistics (top artists, play counts, etc.) but **never leaves the HTML file**
- No telemetry, no tracking, no third-party analytics
- GitHub / X links in the footer point to the project — replace them with your own if you publish your report

---

## About the name

"Resonance" — the phenomenon where one vibration reinforces another at the same frequency. Your library is 901 tracks (or 5,000, or 20,000). Most of them sit still. The ones that resonate are the ones you return to, again and again, often without noticing.

---

## Acknowledgments

- Design system: [Anthropic Claude Design](https://claude.ai)
- Globe rendering: [globe.gl](https://globe.gl)
- 3D engine: [three.js](https://threejs.org)
- Country data: [Natural Earth](https://www.naturalearthdata.com)
- Album metadata: iTunes Search API

---

## License

MIT
