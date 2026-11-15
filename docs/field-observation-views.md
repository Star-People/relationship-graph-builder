# Field Station evidence in the graph views

The `fieldObservations` catalog section is generated from published machine-data Field Station records. The client deduplicates recordings and follows `reviewed_frame_in` edges for object counts; several observations from one video are not separate corroborating recordings.

- Clock: diamonds show recording **start times in UTC**, alongside documentary time-mention circles. These are not exact sighting times. The time-period and collection filters apply to Field Station records; CSV exports include their Archive evidence links.
- Signals: a separate recording list opens Archive bundles and measured RF previews. A preview downloads at most 32 MiB and checks the expected byte size and SHA-256 before parsing. Snapshot selection preserves missing bins. The plot uses receiver dB, not calibrated dBm, and is separate from the documentary mention-count axis. Unavailable, oversized, changed, or CORS-blocked files retain download links and an explicit error.
- Map: public county polygons represent coarse observation regions. No station-coordinate pin is created. Selecting a county switches the evidence filter to Field Station and focuses the region. Unknown locations remain in the recording list.

`data/field_location_reviews.json` records an operator confirmation for exactly 579 existing observation IDs on 2026-11-15. It does not assign a default location to the station or to future observations. Conflicting known capture metadata fails the build. Located-in edges preserve the review ID and review-file SHA-256.

`data/field_regions.json` contains the public 2026 Census TIGERweb San Mateo County boundary (GEOID 06081), simplified by the Census endpoint and rounded to four decimal places. Its centroid is only a map-view target, never a station location. The source query is retained with the geometry.

## Validation

- 222 Python tests and 182 JavaScript tests.
- Required `--require-data` catalog rebuild against pinned machine-data `315d81ac0ac9a42ececc9ca0fb3a8e18c06ad8ad` (545 observations and five real claim-bearing documents).
- Current HQ projection: 579 observations, 883 reviewed objects, 316 recordings, one county region.
- Desktop 1440×960 and mobile 390×960 before/after screenshots under `screenshots/`.
- Browser interaction checks: clock marks, document/Field Station filtering, UTC inspectors, county focus, and a real Archive RF download with checksum verification.

Preview runs on HQ loopback at `http://127.0.0.1:4187/`. Select Clock, Signals, or Map. No remotely reachable Tailnet preview is claimed: the current Tailscale Serve daemon configuration requires administrator access. The screenshots provide reviewable visual evidence.
