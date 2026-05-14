# Handoff — Apple Music Library Editorial Report

This is a handoff for a fresh Claude window picking up work on `report.html`. The previous window's context was getting long. Everything in this doc is true as of commit `b232f53`.

## What this project is

An Apple Music library analyzer + a single-file editorial HTML report.

Pipeline:
1. `extract_library.js` (JXA) reads the user's Apple Music library → `data/library.json` (901 tracks).
2. `analyze_library.py` derives obsession index / forgotten shelf / monthly timeline / artist geography → `data/analysis.json`.
3. `report.html` is a self-contained editorial scroll that renders curated data into 7 narrative sections.
4. `fetch_artwork.py` (iTunes Search API) pre-fetches album cover URLs for the curated tracks → `data/artwork.json`.
5. `verify_candidates.py` is the gate for any *new music recommendations* — requires (a) iTunes Search artist+track soft-match AND (b) NOT already in `library.json`.

The user is **Clickist** — a developer + content creator. They prefer Chinese conversation with English code/identifiers, conclusion-first answers, no sycophancy. They push back when something isn't right, and they expect the same from Claude.

## Files

```
.
├── CLAUDE.md                       # project instructions (read this first)
├── report.html                     # THE artifact — single self-contained file
├── analyze_library.py              # JXA-driven analysis → data/analysis.json
├── extract_library.{js,sh}         # JXA extractor for Apple Music
├── fetch_artwork.py                # iTunes Search API → data/artwork.json
├── verify_candidates.py            # iTunes + library exclusion gate (recs)
├── artist_countries.json           # manual artist → country lookup
├── claude_design/
│   ├── DESIGN.md                   # Anthropic Claude design system (the bible)
│   └── README.md
├── data/
│   ├── library.json                # raw extract (440K)
│   ├── analysis.json               # analysis output (324K)
│   ├── artwork.json                # iTunes CDN URLs per (artist|track), 48 entries
│   └── recent_vein_candidates.json # verify_candidates.py output (debug/audit)
└── docs/
    ├── content_spec.md             # original finalized S1–S7 content spec
    └── handoff.md                  # this file
```

## Strict conventions

**These are non-negotiable. Violating them means the work has to be redone.**

1. **DESIGN.md is the source of truth.** Every color, font, radius, spacing, component pattern comes from `claude_design/DESIGN.md`. Do not approximate. Do not inline hex values that aren't in the design system. Use the CSS custom properties at the top of `report.html`.

2. **Light and dark are two independent themes.** No surface mixing. A light page does not contain dark surfaces, and vice versa. The dark navy `code-window-card` (used in S7) and the always-coral primary CTA are the only cross-mode constants. The cream stack (canvas, surface-soft, surface-card, surface-cream-strong) shifts entirely between modes.

3. **Default theme follows system** via `prefers-color-scheme`. Toggle button overrides session-only (no localStorage).

4. **Coral is the brand voltage — scarce.** DESIGN.md: "Reserve coral for primary CTAs and full-bleed callout-card-coral moments. Don't paint accent moments coral elsewhere." The hero now-card is coral (sanctioned exception we made deliberately — the user wanted the hero diptych balanced). S4 callout is coral. Active-country fill on globe is coral. Country-code chips are coral. Recent Vein thumb's hover ring is coral. That's the full coral budget. Don't add more.

5. **Single file.** All HTML, CSS, JS, and inlined data live in `report.html`. No build step, no bundler, no node_modules. External assets the page references at render time: Google Fonts; globe.gl + three.js from unpkg; Natural Earth geojson from unpkg/github-raw; iTunes Music CDN (`is*-ssl.mzstatic.com`) for cover thumbnails. Vendoring these locally is a deferred task — see "What's likely next".

6. **Conversation in Chinese, code/identifiers English.** Conclusions first. No "great question!" preamble. Push back if the user's idea has a tradeoff they should hear about.

7. **Discuss before risky implementation.** If the user says "讨论" or "对齐" or asks for an opinion, do not start coding. Reply with options + a recommendation. The user usually approves with "可以" / "开干" / "按你说的办" before implementation.

8. **Data integrity — NEVER invent tracks.** This bit us hard. The previous window's S7 curation included ~8 fabricated track names (artists existed in `library.json`, specific track titles did not). Three rules now stand:

   - **Anything claimed to be "from the user's library" must verify against `library.json` (exact or near-exact match on artist + name).** If you can't find it, it doesn't exist. Do not pattern-complete plausible-sounding tracks from real artists.
   - **Anything claimed to be a "new recommendation" must pass `verify_candidates.py`**: iTunes Search soft-match on artist + track AND library.json exclusion.
   - **iTunes Search API ≠ Apple Music.** The user's Apple Music app uses a much larger catalog (full Apple Music subscription tier). iTunes Search is a free public endpoint with a *subset*. So "not on iTunes Search" doesn't mean "not on Apple Music" — but it does mean we can't programmatically verify. When iTunes Search misses, we either (a) hand-substitute the right album-level artwork URL after manual inspection, (b) leave artwork null and render placeholder, or (c) drop the track.

## Tech stack

- Vanilla HTML/CSS/JS — no framework
- Fonts: EB Garamond (display serif), Inter (body sans), JetBrains Mono (code), all via Google Fonts
- Globe rendering: `globe.gl@2.32.4` + `three@0.155.0` from unpkg CDN
- Country geojson: `three-globe`'s example `ne_110m_admin_0_countries.geojson` from unpkg, fallback to GitHub raw
- Album covers: pre-resolved iTunes Music CDN URLs (mzstatic.com), pre-baked into the inline DATA
- All structural data inlined in `<script id="DATA" type="application/json">` — fresh agent should not assume external data fetches at render time (images and globe assets are the only network requests)
- IntersectionObserver drives the S3 timeline axis sync and the S5 globe POV / active-country sync

## Current state of each section

**S1 — Hero** ✅
- Display-serif headline ("Your play count is a diary you never meant to publish.") at clamp(36, 5.4vw, 64px), 3 lines on desktop
- Italic body-lead paragraph below
- Right side: full coral now-card (matches S4 callout treatment) showing the most recently added track (Mac DeMarco / Chamber of Reflection)
- Now-card has a 56px album thumb in the head, **right** of track-name + artist (moved to the right in `b232f53` per user preference; was initially on the left). The title block has `flex: 1` to push the thumb against the card's right edge. Translucent white inner-ring (`color-mix(in srgb, var(--on-primary) 22%, transparent)`) + soft drop shadow defines it against coral.
- Meta-strip below: 4 stats in a full-width row with a hairline above
- Hero container capped at 1150px (other sections use 1200px) so the diptych reads centered

**S2 — Obsession Archive** ✅ (covers added; rest visually untouched, may need polish)
- 2-col: Top artists (left) + Top tracks (right), 10 entries each, display-serif rank numbers
- **Top-tracks rows** now have a 44px album thumb between rank number and text (since `a56f71d`). Grid template `56px 44px 1fr auto`. Top-artists rows don't get thumbs (no canonical artist cover).
- Editorial commentary below in 4 annotated blocks
- The `is-highlight` coral primary-line is applied to Harry Styles rows (tracks tab) and top-4 artists by hardcoded list

**S3 — Timeline** ✅ (polished)
- Sticky-scroll: left axis (years 2020-2026) is `position: sticky`, right event stream flows
- IntersectionObserver tracks the centered event card and lights up the corresponding year dot + updates the "LISTENING" card at the bottom of the axis
- Year dot: 6px coral, `left: 2px` (visual midpoint between hairline and year text)
- "LISTENING" card has `min-height: 100px` so 1-line titles don't reflow the years column above
- Vertical hairline runs the full height of the axis container
- Inactive year dots are `opacity: 0`

**S4 — Forgotten Shelf** ✅ (polished, covers added)
- Top: 2-col grid. Left = lead text + 2 stat tiles (117 never played / 512 cold 12mo). Right = coral callout with the giant decorative quote mark
- Bottom: ghost-list lifted to full-width below the grid, displayed as a 2-col CSS Grid of ghost rows. Top hairline applied per-column via `:nth-child(-n+2)` so it segments at the column-gap
- **Each ghost row** now has a 56px album thumb left of the name (since `a56f71d`). Default state: `filter: grayscale(0.35) opacity(0.78)` — quietly faded, evoking forgottenness. **Hover restores full color** so the reader can see the actual cover.

**S5 — Geography (globe)** ✅ (heavily polished + WebGL fallback)
- globe.gl globe in a sticky-scroll geo-stage on the left
- Right side: country narrative cards (US, JP, GB, AU, SE, TW, CN, BY, EC)
- IntersectionObserver flips the active card AND updates `ACTIVE_COUNTRY_CODE`, which triggers `polygonCapColor` to paint that country coral
- No floating bubble label — country name is rendered as bottom-left coral display-serif chyron inside the geo-stage. Taiwan card label is "Chinese Taiwan" per user request (geopolitical), but the geojson name-match fallback in `featureMatchesCode` still uses lowercase `'taiwan'` because Natural Earth's geojson labels the entity that way — **do not change that**.
- No coral atmosphere — `showAtmosphere(false)`
- No point cylinders, no propagating rings — the country fill itself is the marker
- Country borders: `polygonStrokeColor` uses the water color at 55% alpha (helper: `hexToRgba`)
- Land color in light mode: `#3d3d3a` (body color — warm dark grey, not near-black)
- Active card uses `box-shadow` for "悬浮感", no coral border. Theme-aware tokens: `--shadow-active`, `--card-active-bg`
- `featureMatchesCode(feature, code)` handles the three Natural Earth entries marked `-99`: Taiwan, Belarus, Ecuador — falls back to name match
- **WebGL probe in `initGlobe()` (since `a56f71d`)**: creates a throwaway `<canvas>` and tries to get a 2D WebGL context. If it fails (hardware acceleration off, GPU sandboxed, etc.), the globe container gets `.is-fallback` class and a graceful text fallback ("Globe rendering requires WebGL. Enable hardware acceleration..."). Critically, this prevents an uncaught throw from `Globe()()` from killing the rest of the inline script — without this fix, S6/S7 wouldn't render on a GPU-disabled browser. Belt + suspenders: the actual init call is also wrapped in try/catch.

**S6 — Portrait** ✅ (visually untouched since initial commit, may need polish)
- Editorial closing paragraphs + 3 trait cards (30% / 27% / 0)

**S7 — Playlists** ✅ (data rebuilt, covers added, AppleScript generator upgraded)
- 3 tab panels: Forgotten Awakening / Recent Vein / Obsession Replay
- **Track rows now have a 40px album thumb** between checkbox and text (since `a56f71d`). Grid template `24px 40px 1fr auto`.
- **Forgotten Awakening (8 tracks)** — pulled from `analysis.json.forgottenShelf` (real, grounded data). Diverse by genre (J-Pop / Folk / Christmas / Anime / Pop). Skips the K-On binge already over-represented in S4.
- **Recent Vein (8 tracks)** — *recommendations of NEW music*. Each track:
  - Verified via `verify_candidates.py` (iTunes Search soft-match + library exclusion)
  - Has an `appleUrl` field pointing to its Apple Music page
  - **Cover thumb is a click-through link** to that Apple Music URL (`<a class="track-thumb-link">`), with a coral ring on hover
- **Obsession Replay (10 tracks)** — direct top-10 from `obsessionIndex.topTracks`. All real, all in library.
- "Generate AppleScript" button → `buildAppleScript` now **split-handles** library tracks vs. recommendations:
  - Library tracks (no `appleUrl`): existing `whose name is X and artist is Y` pattern → duplicates into new playlist
  - Recommendation tracks (has `appleUrl`): emits `open location "URL"` per track → opens Apple Music app to each track page so user can tap "+"
  - For a pure-recommendation playlist (current Recent Vein), no local playlist is created; for a pure-library playlist (Forgotten Awakening / Obsession Replay), no URLs are opened; mixed playlists do both

## Data integrity — how each S7 playlist is constructed

This is the most important architectural fact about S7. The previous window's tracklist was ~33% fabricated. The new system:

| Playlist | Source | Verification |
|---|---|---|
| Forgotten Awakening | `analysis.json.forgottenShelf.neverPlayed` + `.longUnplayed` | Implicit — these come from JXA extraction of the user's actual library, so they exist by construction |
| Recent Vein | Hand-curated candidate pool in `verify_candidates.py` | Gated: iTunes Search artist+track soft-match AND library.json exclusion |
| Obsession Replay | `analysis.json.obsessionIndex.topTracks` | Implicit (same as Forgotten Awakening) |

For Recent Vein, the verification gate is critical. The 2026-05-14 audit:

```
candidates submitted: 34
passed all gates:     20  (kept 8 for the playlist)
not on iTunes Search: 14  (mostly Japanese hip-hop scene — Fat Jon,
                            Uyama Hiroto, Force of Nature, Substantial,
                            Cradle, Cise Starr, Funky DL — also Frank
                            Ocean, whose catalog is famously absent
                            from iTunes Search)
```

So the 8 Recent Vein picks land lighter on the lo-fi Japanese strand than the narrative would ideally want, because the catalog gap is real. Workable substitutes (Bonobo, Tycho, Khruangbin) shifted the mix toward broader downtempo/instrumental.

## Token map (the cream stack)

Light mode shifts one notch warmer than DESIGN.md's canonical values to match the Anthropic wordmark plate:
```
--canvas:              #f5f0e8  (was #faf9f5)
--surface-soft:        #efe9de  (was #f5f0e8)
--surface-card:        #e8e0d2  (was #efe9de)
--surface-cream-strong:#ddd3c1  (was #e8e0d2)
--hairline:            #ddd3c1
--hairline-soft:       #e6dccd
```

Dark mode is unchanged from DESIGN.md canonical (canvas `#181715` etc.).

Other theme-aware tokens that matter:
- `--card-active-bg` (active state bg for cards)
- `--shadow-active` (active state drop shadow)
- `--globe-water` / `--globe-land` / `--globe-marker` / `--globe-atmosphere`
- `--code-bg` / `--code-bg-soft` / `--code-fg` / `--code-fg-soft` (always-dark surfaces — same intent both modes)

## Commit history (most recent first)

```
b232f53  Perf: pause Globe offscreen, drop nav backdrop-filter past hero
7f23fe9  Update handoff to a56f71d state
a56f71d  Album covers across S1/S2/S4/S7; rebuild S7 playlists from real data
6f661d8  Drop chapter eyebrows; rename Taiwan to Chinese Taiwan
bb1842d  S5 geography: coral code chip, serif label, paint active country
00e8819  S5 geography: drop coral atmosphere, soften light-mode land
9ce9121  S5 geography: card shadow + country borders
752ebdd  S3 axis dot + S4 ghost list polish
72b88f2  S3 timeline axis: lock card height, hide idle year dots, rename label
11197e1  S1 polish: drop label, retune card sizing, narrow hero inset
20ba8b7  S1 now-card: switch to coral surface
cdb9207  S1 hero rebalance + warmer cream stack
7884ef7  Initial commit: Apple Music library analyzer + editorial HTML report
```

`git reset --hard <sha>` is the user's preferred rollback when an experiment doesn't work — they explicitly said they trust git for this.

## What's likely next

User explicitly **parked** these three after the perf-audit pass (2026-05-15) and said "记入 handoff 不着急" — so all three are queued, none urgent. Address only when the user surfaces them again.

- **S2 (Obsession Archive)** visual polish — covers added (44px thumbs in top-tracks), but rank rows / editorial annotations / `is-highlight` coral usage are still in their initial form. Candidates for revisit: rank-num typographic weight against thumb, annotation block layout, the hardcoded highlight-artist list (Sia / Avicii / Nujabes / Harry Styles / Otaki) at L1822.
- **S6 (Portrait)** visual polish — completely untouched. 3 trait cards (30% / 27% / 0) and 3 closing editorial paragraphs. Mostly typographic and rhythm work; the data is fine.
- **Vendor globe assets locally** — three.js + globe.gl + geojson currently load from unpkg + github raw. User explicitly said "到最后再来解决" (memory `project-vendor-globe` tracks this). Trigger when the user says "收尾" / "vendoring" / "globe 还是不稳". Notes: (a) does NOT solve WebGL-disabled-browser issues (separate fallback path already exists, do not remove); (b) breaks the "single file" property if files are added — discuss with user whether to accept multi-file delivery or base64-inline the geojson (~150KB acceptable, scripts are larger).
- **Remaining perf opportunities (audit-surfaced, not acted on)** — the 2026-05-15 perf audit identified two more medium-impact wins that the user chose NOT to do in the current pass. Surface again only if perf complaints return. (a) **Smaller cover variants** — all 48 album thumbs request `600x600bb.jpg` (~56 KB ea) but render at 40-56 CSS px. Swapping to `200x200bb.jpg` (~12 KB) cuts total artwork transfer from ~2.7 MB to ~580 KB. One regex substitution across the inline DATA. Keep the hero now-card at 600 (only 1 image, dominant visual). (b) **Globe polygon re-render efficiency** — every country-card IO callback creates a new arrow function for `polygonCapColor`, which makes globe.gl re-evaluate the accessor for all ~177 polygons. Could bind the accessor once and mutate state via a closure. Medium impact, mostly noticeable during fast scroll through S5.

## Gotchas / non-obvious things

- **`featureMatchesCode`** is needed because Natural Earth marks Taiwan/Belarus/Ecuador as `ISO_A2: -99`. Don't drop the fallback name match if you refactor the function. Specifically, `TW: 'taiwan'` matches against the geojson's own `ADMIN`/`NAME` property — this is comparing against external data, **do not rename to `'chinese taiwan'`** even though the user-facing label uses that.
- **`ACTIVE_COUNTRY_CODE`** is a module-level `let` captured by the polygon color accessor. The accessor is re-set inside the IntersectionObserver to force globe.gl to re-render. If you change how the accessor is set, make sure both the initial load AND the scroll handler set it via the same pattern.
- **Globe CDN dependencies** — three.js + globe.gl + geojson all load from unpkg. If the user's proxy/VPN goes down, the globe will be a blank black sphere with `ERR_PROXY_CONNECTION_FAILED` in the console. This is not a code bug. See "What's likely next" for the vendoring task.
- **WebGL probe** — `initGlobe()` does a quick `canvas.getContext('webgl')` test. If null, sets `#globe.is-fallback` and returns early. **Don't remove this probe** — without it, an uncaught throw in three.js's WebGLRenderer constructor will kill the rest of the inline script (including S6/S7 rendering). Confirmed in 2026-05-14: a user with hardware acceleration disabled hit this exact path.
- **Globe pause when offscreen** (since `b232f53`) — `watchGlobeVisibility` IIFE near the end of the script observes `.geo-stage` and calls `GLOBE.pauseAnimation()` / `resumeAnimation()` + toggles `controls.autoRotate`. **Don't remove or simplify** — globe.gl's rAF loop is the dominant idle GPU cost and was directly responsible for the user's laptop fan running constantly. The feature-detect on pauseAnimation is intentional (so an older bundled globe.gl version degrades gracefully). The `if (!GLOBE) return` guard at top is what makes this safe in the WebGL-fallback path.
- **Top-nav `is-scrolled` class** (since `b232f53`) — a passive scroll listener with rAF throttling toggles `.is-scrolled` on `.top-nav` past 80px. The class removes `backdrop-filter` and switches to opaque `var(--canvas)` background. **Don't drop this** — backdrop-filter: blur(12px) was the second-largest scroll-time cost. The glassy nav is preserved over the hero (good aesthetic) and dropped during reading (good perf). The 80px threshold sits well within the hero region.
- **`.tl-axis__nowat`** card has `min-height: 100px` to lock its 2-line footprint. Don't remove this — without it, the year markers above redistribute on every scroll-in.
- **Ghost list top border** is per-column via `:nth-child(-n+2)` because the parent's full-width `border-top` would cross the column-gap and look wrong with the segmented bottoms.
- **Coral on coral**: don't put coral text on the coral hero card or S4 callout. White-with-opacity (`color-mix(in srgb, var(--on-primary) 80%, transparent)`) is the secondary-text pattern there.
- **Theme transition timing** — body uses `transition: background-color .35s ease, color .35s ease`. Some elements have their own transitions that need to match this duration if you're animating other properties at the same time.
- **iTunes Search misses for indie/Japanese hip-hop** — for tracks where iTunes Search returns no result but the album is on iTunes (e.g., Nujabes / Tinted Eyes — iTunes Search returns nothing for the track but the album "Spiritual State" is there), you can hand-substitute the album-level artwork URL in `data/artwork.json`. The fetcher (`fetch_artwork.py`) skips cached non-null entries by default, so manual overrides are preserved across re-runs.
- **`fetch_artwork.py` track list must stay in sync with inline DATA** — the script's hardcoded `S1_NOW_CARD` / `S2_TOP_TRACKS` / `S4_GHOST_TRACKS` / `S7_*` lists mirror what's curated in `report.html`'s inline DATA. If you change one, change the other. The script is incremental (skips cached entries), so adding a track is cheap.
- **Chinese Taiwan** — user asked for this label to avoid issues. The 3 visible mentions in `report.html` (S3 timeline cards × 2, S5 country card name) use "Chinese Taiwan". The internal name-match fallback in `featureMatchesCode` is unchanged — see above. `docs/handoff.md` (this file) and code comments may still say "Taiwan" when referring to external data fact (e.g., Natural Earth labels).

## User's working style — quick reminders

- They want you to **discuss before implementing** when something is non-trivial. Saying "我倾向 A，理由 X / Y" then asking "你定?" is the right shape.
- They commit before risky changes and will say so ("先 commit 一下"). They trust git for rollback.
- They notice details — alignment, spacing, color harmony. When they say "扎眼" or "不协调", they want you to identify the root cause, not paper over it.
- They notice when things are **wrong**. The S7 fabrication near-miss surfaced because they directly questioned a claim ("apple music的歌单,你告诉我itunes没有封面图,那我看的是什么呢?"). When you state a fact, be precise. When you don't know, say so.
- They sometimes use their own section numbering (e.g. "S2底下" when they mean the timeline). Read in context.
- They speak Chinese mostly but mix English freely. Reply in Chinese unless they switch.

## How to verify your work in browser

The previous windows used the `chrome-devtools` MCP tool. If that's not connected to your session, fall back to:

1. Open file:// directly — the user keeps the page open in their browser, just refresh (Cmd+Shift+R for hard reload).
2. If you need automated capture: `webapp-testing` skill provides Playwright (note: requires `pip install playwright` + `playwright install chromium` — a global install that you should ask the user to approve first, since this crosses the "no system modification" line in user's CLAUDE.md).
3. For a `localhost` URL that avoids the file:// CORS warnings: `python3 -m http.server 8000` from the project root, then open `http://localhost:8000/report.html`.

If the user says "不用截图了" or similar, just edit and trust your math.

## Skills used in recent windows

- `awesome-design` (initially, to pull in the Claude DESIGN.md — already done, file is at `claude_design/DESIGN.md`)
- `frontend-design` (for the quality bar — production-grade, refined motion, intentional design)
- `webapp-testing` (Playwright — for cases where the user wants automated verification)

Re-invoking these for major new work is fine but unnecessary for incremental polish.
