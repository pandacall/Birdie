from pathlib import Path

from birdie.config import load_config
from birdie.gate import Rule
from birdie.models import Category, PostingMode, Window


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


def test_rules_and_default_mode_parse(tmp_path: Path) -> None:
    cfg_file = tmp_path / "birdie.toml"
    cfg_file.write_text(
        'page_id = "1"\n'
        'default_posting_mode = "review"\n'
        "\n"
        "[[rules]]\n"
        'kind = "contains_multikill"\n'
        "min_streak = 5\n"
        'mode = "auto"\n'
        "\n"
        "[[rules]]\n"
        'kind = "peak_category"\n'
        'category = "blooper"\n'
        'mode = "review"\n'
    )

    cfg = load_config(cfg_file)

    assert cfg.default_mode == PostingMode.REVIEW
    assert cfg.rules == [
        Rule(kind="contains_multikill", mode=PostingMode.AUTO, min_streak=5),
        Rule(kind="peak_category", mode=PostingMode.REVIEW, category=Category.BLOOPER),
    ]
