from sentinel.cli import build_parser, main


def test_list_datasets(capsys):
    assert main(["list-datasets"]) == 0
    out = capsys.readouterr().out
    assert "auair" in out and "geotagged" in out


def test_no_command_prints_help(capsys):
    assert main([]) == 0
    assert "usage" in capsys.readouterr().out.lower()


def test_demo_smoke(tmp_path):
    cfg = tmp_path / "c.yaml"
    out = tmp_path / "out"
    cfg.write_text(
        "scene:\n  width: 320\n  height: 240\n  num_objects: 4\n"
        f"output_dir: {out}\n"
    )
    assert main(["demo", "--config", str(cfg)]) == 0
    assert (out / "metrics.json").exists()


def test_parser_has_subcommands():
    parser = build_parser()
    assert [a for a in parser._actions if a.dest == "command"]
