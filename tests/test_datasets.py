import json

import pytest

from sentinel.datasets import (
    geotagged_datasets,
    get_dataset,
    is_available,
    list_datasets,
    parse_flight_log,
    require,
)


def test_registry_has_geotagged_entries():
    keys = {d.key for d in list_datasets()}
    assert {"auair", "seadronessee", "uavdt", "visdrone"} <= keys
    assert len(geotagged_datasets()) >= 5
    assert any(not d.geotagged for d in list_datasets())


def test_get_unknown():
    with pytest.raises(KeyError):
        get_dataset("nope")


def test_parse_flight_log(tmp_path):
    path = tmp_path / "log.json"
    path.write_text(json.dumps({"lat": 18.52, "lon": 73.85, "altitude": 90, "heading": 45}))
    log = parse_flight_log(path)
    assert log["lat"] == 18.52 and log["altitude"] == 90 and log["heading"] == 45
    assert log["depression"] == 60.0   # default


def test_parse_flight_log_missing_keys(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text(json.dumps({"lat": 1.0}))
    with pytest.raises(ValueError):
        parse_flight_log(path)


def test_require_missing(tmp_path):
    assert is_available("auair", tmp_path) is False
    with pytest.raises(FileNotFoundError):
        require("auair", tmp_path)
