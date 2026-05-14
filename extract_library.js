// JXA script: Extract Apple Music library → JSON
// Run with: osascript -l JavaScript extract_library.js

function run() {
  const Music = Application("Music");
  const lib = Music.libraryPlaylists[0];
  const tracks = lib.tracks();

  const fmt = (d) => {
    if (!d || d.toString() === "missing value") return null;
    try { return new Date(d).toISOString(); } catch(e) { return null; }
  };

  const safe = (v, fallback) => {
    try {
      const val = v();
      if (val === undefined || val === null || val.toString() === "missing value") return fallback;
      return val;
    } catch(e) { return fallback; }
  };

  const data = tracks.map((t) => ({
    name:        safe(() => t.name(), ""),
    artist:      safe(() => t.artist(), ""),
    album:       safe(() => t.album(), ""),
    albumArtist: safe(() => t.albumArtist(), ""),
    genre:       safe(() => t.genre(), ""),
    composer:    safe(() => t.composer(), ""),
    playCount:   safe(() => t.playedCount(), 0),
    skipCount:   safe(() => t.skippedCount(), 0),
    rating:      safe(() => t.rating(), 0),
    loved:       safe(() => t.loved(), false),
    disliked:    safe(() => t.disliked(), false),
    duration:    safe(() => t.duration(), 0),
    bpm:         safe(() => t.bpm(), 0),
    year:        safe(() => t.year(), 0),
    trackNumber: safe(() => t.trackNumber(), 0),
    dateAdded:   fmt(safe(() => t.dateAdded(), null)),
    lastPlayed:  fmt(safe(() => t.playedDate(), null)),
  }));

  const outPath = "/Users/clickist/Desktop/music-analyzer-skill/data/library.json";
  const json = JSON.stringify(data, null, 2);

  const FileManager = $.NSFileManager.defaultManager;
  const nsStr = $.NSString.alloc.initWithUTF8String(json);
  nsStr.writeToFileAtomicallyEncodingError(outPath, true, $.NSUTF8StringEncoding, null);

  return `Extracted ${data.length} tracks → ${outPath}`;
}
