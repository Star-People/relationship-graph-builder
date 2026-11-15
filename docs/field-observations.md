# Field Station observation graph

The catalog now imports `Field-Station/<station-id>/<capture-event-id>.json` from
its pinned machine-data checkout. `scripts/field_observations.py` builds a separate
`catalog.fieldObservations` graph; transcript entities, document counts, claims,
frequency mentions and their ranking are unchanged.

## Nodes and relationships

| Node | Relationships |
| --- | --- |
| Observation | observed_by Station; captured_in Recording; has_reviewed_object ReviewedObject |
| Observation | evidenced_by ArchiveBundle; predicted_by Model; located_in CountyRegion |
| ReviewedObject | reviewed_frame_in Recording, with the original frame index |

Identifiers are stable and namespaced. Shared recordings, stations, models and
Archive items are deduplicated. Two crops or detection events in one recording
are not independent corroborating sources. No identity link to historical
transcript entities is invented from similar names, locations or appearance.

Each edge carries the exact machine-data path, source-file SHA-256, observation
ID, source journal epoch and revision. Archive evidence retains reviewed-bundle
revision, verification time, file size, SHA-256 and URLs for original video,
reviewed frames, annotations and RF assets. No media is copied into the catalog.

`predicted_by` preserves the original capture model's classification and score,
which can disagree with the later human review. A score is not reinterpreted as
a calibrated probability. Human `anomalous` means reviewed as anomalous; it is
not a claim about the object's physical identity or cause.

## Corrections, privacy and time

Only `published` records enter the active graph. `withdrawn` and
`pending_evidence` records contribute status counts and the input fingerprint,
but no nodes or edges. Rebuilding derives the complete projection from current
records, so previous relationships do not survive a review correction. Invalid
active evidence fails the build instead of silently disappearing.

The output is constructed from an allowlist. County, state and country can form
a region node; coordinates, local filesystem paths and private notes are not
copied. Unknown location remains unlocated. County regions are not geocoded to
points, and proximity is not inferred.

Recording start/end times describe recording coverage, not exact object arrival
or sighting duration. Annotation frame indexes remain in the original recording's
coordinate system, even when an Archive video has been trimmed. No frame/time
conversion is attempted without an explicit timing map. Review timestamps remain
separate. CE5 playback is measured recording context (on, off or unknown), not a
causal edge. RF assets are links to measurements, not documentary frequency mentions.

## Build and publication

The standard `scripts/build_catalog.py --input <machine-data> --require-data`
build imports this section automatically, after transcript extraction and before
writing catalog artifacts. It reads current JSON on every assembly; transcript
extraction cache hits cannot freeze observation reviews. Existing section sharding
bounds generated files, and the browser's generic section loader rehydrates them.
Changes to the adapter trigger catalog validation/rebuild in GitHub Actions.

This is the data integration layer. Existing graph views still render their
existing transcript data; a dedicated observation explorer is not part of this
change. Consumers can use `fieldObservations.nodes`, `.edges`, `.observations`,
`.counts`, `.input` and `.policy` from the hydrated catalog. Catalog-wide counts
include `fieldObservations` and `fieldReviewedObjects` separately from documents.

## Verification

Tests cover identity/evidence binding, conflicting machine/human labels, shared
recording deduplication, withdrawal and pending states, private-field exclusion,
invalid source rejection, deterministic generation, integration without changing
document counts, and a complete section-shard round trip.
