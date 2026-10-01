from sentinel.config import SentinelConfig
from sentinel.pipeline import SentinelPipeline, run_demo


def _cfg():
    cfg = SentinelConfig()
    cfg.scene.width = 320
    cfg.scene.height = 240
    cfg.scene.num_objects = 5
    return cfg


def test_demo_runs_and_geolocates(tmp_path):
    summary = run_demo(_cfg(), out_dir=tmp_path)
    assert summary["ground_truth"] > 0
    assert summary["geolocated"] > 0
    assert summary["median_error_m"] is not None
    assert summary["median_error_m"] < 25.0
    assert (tmp_path / "metrics.json").exists()
    assert (tmp_path / "detections.geojson").exists()


def test_true_attitude_mode(tmp_path):
    cfg = _cfg()
    cfg.attitude_source = "true"
    summary = run_demo(cfg, out_dir=tmp_path)
    assert summary["attitude_source"] == "true"
    assert summary["depression_error_deg"] == 0.0


def test_pipeline_reusable(tmp_path):
    pipeline = SentinelPipeline(_cfg())
    first = pipeline.run(out_dir=tmp_path)
    second = pipeline.run(out_dir=tmp_path)
    assert first["ground_truth"] == second["ground_truth"]
