from pathlib import Path

from birdie.config import load_config
from birdie.models import Window


def test_minimal_config_defaults_to_16x9_video_profile(tmp_path: Path) -> None:
    cfg_file = tmp_path / "birdie.toml"
    cfg_file.write_text('page_id = "123"\n')

    cfg = load_config(cfg_file)

    assert cfg.page_id == "123"
    assert cfg.output_profile.name == "video"
    assert (cfg.output_profile.width, cfg.output_profile.height) == (1920, 1080)
    assert cfg.output_profile.max_seconds is None


def test_explicit_values_override_defaults(tmp_path: Path) -> None:
    cfg_file = tmp_path / "birdie.toml"
    cfg_file.write_text(
        'page_id = "999"\n'
        "\n"
        "[output_profile]\n"
        'name = "reel"\n'
        "width = 1080\n"
        "height = 1920\n"
        "max_seconds = 60\n"
        "\n"
        "[skeleton]\n"
        "window_start = 30.5\n"
        "window_end = 45.5\n"
        "\n"
        "[paths]\n"
        'recordings = "D:/rec"\n'
        'compilations = "D:/out"\n'
        "\n"
        "[tuning]\n"
        "merge_gap = 4.0\n"
        "length_budget = 90.0\n"
    )

    cfg = load_config(cfg_file)

    assert cfg.output_profile.name == "reel"
    assert (cfg.output_profile.width, cfg.output_profile.height) == (1080, 1920)
    assert cfg.output_profile.max_seconds == 60
    assert cfg.skeleton_window == Window(start=30.5, end=45.5)
    assert cfg.recordings_dir == Path("D:/rec")
    assert cfg.compilations_dir == Path("D:/out")
    assert cfg.merge_gap == 4.0
    assert cfg.length_budget == 90.0
