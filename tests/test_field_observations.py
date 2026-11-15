import copy
import json
import tempfile
import unittest
from pathlib import Path
from scripts.field_observations import load_field_observations
from scripts.build_catalog import build, write_catalog_section_shards


class FieldObservationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.event = "a" * 32
        self.recording = "20261112T130346Z-d036dc"
        self.family = "field-recording:station-1:" + self.recording
        self.path = self.root / "Field-Station/station-1" / (self.event + ".json")
        self.path.parent.mkdir(parents=True)
        self.record = {
            "schema": "ufo-files-field-observation/v1", "id": "field:station-1:" + self.event,
            "station_id": "station-1", "capture_event_id": self.event,
            "revision": 1, "source_epoch": "b" * 32, "status": "published",
            "human_classification": "anomalous", "review_scope": "human_reviewed_objects",
            "recordings": [{"id": self.recording, "source_family_id": self.family,
                            "capture_kind": "automatic", "started_epoch": 1000, "stopped_epoch": 1060, "video_fps": 60}],
            "annotations": [{"id": "c" * 32, "classification": "anomalous", "reviewed_epoch": 9000,
                             "bounds_pixels": [10, 20, 64, 64], "crop_sha256": "d" * 64,
                             "frame_references": [{"recording_id": self.recording, "original_frame_index": 12}]}],
            "archive_bundles": [{"recording_id": self.recording, "identifier": "example-item",
                                 "url": "https://archive.org/details/example-item", "verified_epoch": 10000,
                                 "review_revision": "e" * 64, "assets": [{"name": "video.mp4", "bytes": 123,
                                 "sha256": "f" * 64, "url": "https://archive.org/download/example-item/video.mp4"}]}],
            "location": {"status": "known", "precision": "county", "county": "San Mateo", "state": "CA", "country": "USA"},
            "original_prediction": {"scope": "original_capture_prediction", "model_sha256": "0" * 64,
                                    "classification": "not_anomalous", "score": .1},
            "ce5_playback": {"state": "unknown"},
        }
        self.save()

    def save(self):
        self.path.write_text(json.dumps(self.record))

    def test_typed_graph_has_bound_evidence_and_distinct_review_prediction(self):
        graph = load_field_observations(self.root)
        self.assertEqual(graph["counts"]["observations"], 1)
        nodes = {n["id"]: n for n in graph["nodes"]}
        for edge in graph["edges"]:
            self.assertIn(edge["source"], nodes)
            self.assertIn(edge["target"], nodes)
            self.assertEqual(edge["provenance"]["revision"], 1)
            self.assertEqual(len(edge["provenance"]["sourceSha256"]), 64)
        predicted = next(e for e in graph["edges"] if e["relation"] == "predicted_by")
        self.assertEqual(predicted["classification"], "not_anomalous")
        self.assertEqual(nodes[self.record["id"]]["classification"], "anomalous")
        self.assertEqual(nodes[self.family]["startedEpoch"], 1000)
        self.assertEqual(next(n for n in nodes.values() if n["type"] == "reviewed_object")["reviewedEpoch"], 9000)
        self.assertEqual(graph["observations"][0]["ce5Playback"]["state"], "unknown")

    def test_withdrawal_and_pending_remove_all_old_nodes_and_edges(self):
        initial = load_field_observations(self.root)
        for status in ["withdrawn", "pending_evidence"]:
            self.record["status"] = status
            self.record["revision"] += 1
            self.save()
            current = load_field_observations(self.root)
            self.assertEqual(current["counts"][status], 1)
            self.assertEqual(current["nodes"], [])
            self.assertEqual(current["edges"], [])
            self.assertNotEqual(current["input"]["digest"], initial["input"]["digest"])

    def test_shared_recordings_are_not_duplicated(self):
        other = copy.deepcopy(self.record)
        other["capture_event_id"] = "1" * 32
        other["id"] = "field:station-1:" + "1" * 32
        other["annotations"][0]["id"] = "2" * 32
        (self.path.parent / ("1" * 32 + ".json")).write_text(json.dumps(other))
        graph = load_field_observations(self.root)
        self.assertEqual(graph["counts"]["observations"], 2)
        self.assertEqual(graph["counts"]["recordings"], 1)
        self.assertEqual(graph["counts"]["stations"], 1)
        self.assertEqual(sum(n["type"] == "archive_bundle" for n in graph["nodes"]), 1)

    def test_private_data_is_not_projected(self):
        self.record["location"].update(latitude=37.123456789, longitude=-122.123456789)
        self.record["notes"] = "secret private text"
        self.record["archive_bundles"][0]["assets"][0]["private_source"] = "/Volumes/private"
        self.save()
        output = json.dumps(load_field_observations(self.root))
        for forbidden in ["latitude", "longitude", "37.123456789", "secret private text", "/Volumes/private"]:
            self.assertNotIn(forbidden, output)

    def test_malformed_active_evidence_fails_closed(self):
        original = copy.deepcopy(self.record)
        for mutate in [
            lambda r: r.update(revision=0),
            lambda r: r.update(station_id="../../private"),
            lambda r: r.update(schema="unknown"),
            lambda r: r["archive_bundles"][0].update(url="https://evil.example"),
            lambda r: r["archive_bundles"][0]["assets"][0].update(name="../video.mp4"),
            lambda r: r["annotations"][0]["frame_references"][0].update(recording_id="missing"),
            lambda r: r["annotations"][0].update(bounds_pixels=[0, 0, float("nan"), 64]),
        ]:
            self.record = copy.deepcopy(original)
            mutate(self.record)
            self.save()
            with self.assertRaises(ValueError):
                load_field_observations(self.root)

    def test_no_collection_is_explicit_and_symlinks_are_rejected(self):
        self.path.unlink()
        self.path.symlink_to(self.root / "elsewhere.json")
        with self.assertRaises(ValueError):
            load_field_observations(self.root)
        empty = self.root / "empty"
        empty.mkdir()
        result = load_field_observations(empty)
        self.assertFalse(result["input"]["present"])
        self.assertEqual(result["counts"]["records"], 0)

    def test_catalog_integration_keeps_document_counts_and_shards_round_trip(self):
        text = self.root / "Example/example.txt"
        text.parent.mkdir()
        text.write_text(json.dumps({"schema": "ufo-files-archive-ocr/v1", "source_file": "example.pdf"}) + "\n\n" + "NASA investigated Roswell. NASA investigated Roswell. " * 3)
        output = self.root / "output/catalog.json"
        catalog = build(self.root, output, 100, 100, require_data=True)
        self.assertEqual(catalog["counts"]["fieldObservations"], 1)
        self.assertEqual(catalog["counts"]["documents"], 1)
        self.assertFalse(any(d["path"].startswith("Field-Station/") for d in catalog["documents"]))
        self.assertEqual(catalog["signals"]["observations"], [])
        projected = write_catalog_section_shards({"fieldObservations": catalog["fieldObservations"]}, output.parent, min_bytes=1, max_bytes=3000)
        for shard in projected["sectionShards"]:
            payload = json.loads((output.parent / shard["path"]).read_text())
            projected[shard["section"]][shard["field"]].extend(payload["items"])
        self.assertEqual(projected["fieldObservations"], catalog["fieldObservations"])

    def test_import_is_deterministic(self):
        self.assertEqual(load_field_observations(self.root), load_field_observations(self.root))

    def test_operator_confirmation_is_scoped_to_exact_observation_ids(self):
        reviews = self.root / "reviews"
        reviews.mkdir()
        (reviews / "field_location_reviews.json").write_text(json.dumps({
            "schema": "ufo-files-field-location-reviews/v1", "reviews": [{
                "id": "confirmed", "method": "station_operator_confirmation",
                "county": "San Mateo", "state": "CA", "country": "USA",
                "observationIds": [self.record["id"]]}]}))
        self.record["location"] = {"status": "unknown", "precision": "county"}
        self.save()
        graph = load_field_observations(self.root, review_data_dir=reviews)
        edge = next(e for e in graph["edges"] if e["relation"] == "located_in")
        self.assertEqual(edge["locationSource"], "station_operator_confirmation")
        self.assertEqual(len(edge["locationReviewSha256"]), 64)
        self.path.unlink()
        self.record["capture_event_id"] = "9" * 32
        self.record["id"] = "field:station-1:" + "9" * 32
        self.path = self.path.parent / ("9" * 32 + ".json")
        self.save()
        future = load_field_observations(self.root, review_data_dir=reviews)
        self.assertFalse(any(e["relation"] == "located_in" for e in future["edges"]))

    def test_confirmed_region_keeps_county_geometry_separate_from_station(self):
        graph = load_field_observations(self.root)
        self.assertEqual(graph["regions"][0]["geoid"], "06081")
        self.assertIn(graph["regions"][0]["geometry"]["type"], ["Polygon", "MultiPolygon"])
        station = next(n for n in graph["nodes"] if n["type"] == "station")
        self.assertNotIn("lat", station)
        self.assertNotIn("lon", station)
