import pytest

from sentinel.config import SentinelConfig, config_from_dict, load_config, to_dict


def test_defaults():
    cfg = load_config(None)
    assert isinstance(cfg, SentinelConfig)
    assert cfg.scene.altitude > 0
    assert cfg.attitude_source in ("estimated", "true")


def test_yaml_override(tmp_path):
    path = tmp_path / "c.yaml"
    path.write_text("scene:\n  altitude: 200\n  depression: 30\noutput_dir: out\n")
    cfg = load_config(path)
    assert cfg.scene.altitude == 200
    assert cfg.scene.depression == 30
    assert cfg.output_dir == "out"
    assert cfg.detect.blur_kernel == SentinelConfig().detect.blur_kernel


def test_dict_roundtrip():
    cfg = config_from_dict({"scene": {"num_objects": 4}})
    assert to_dict(cfg)["scene"]["num_objects"] == 4


def test_missing_file():
    with pytest.raises(FileNotFoundError):
        load_config("/no/such/file.yaml")
