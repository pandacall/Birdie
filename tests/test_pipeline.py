from pathlib import Path

from birdie.models import OutputProfile, Window
from birdie.pipeline import SkeletonPipeline

from tests.conftest import make_config, make_match
from tests.fakes import FakeCaptioner, FakeEditor, FakePublisher, FakeRecorder


def test_skeleton_runs_record_edit_caption_publish_in_order(tmp_path: Path) -> None:
    log: list[str] = []
    recorder = FakeRecorder(tmp_path / "game.mkv", log=log)
    editor = FakeEditor(log=log)
    captioner = FakeCaptioner(text="Katarina • 18/3/7 • Victory", log=log)
    publisher = FakePublisher(post_id="post-999", log=log)
    cfg = make_config(compilations_dir=tmp_path / "out", skeleton_window=Window(10.0, 25.0))

    pipeline = SkeletonPipeline(
        recorder=recorder,
        editor=editor,
        captioner=captioner,
        publisher=publisher,
        config=cfg,
    )
    result = pipeline.run(make_match(), wait_for_stop=lambda: log.append("wait"))

    assert log == ["start", "wait", "stop", "caption", "render", "publish"]
    assert result.post_id == "post-999"


def test_skeleton_renders_planned_window_with_16x9_profile(tmp_path: Path) -> None:
    recorder = FakeRecorder(tmp_path / "game.mkv")
    editor = FakeEditor()
    cfg = make_config(
        compilations_dir=tmp_path / "out",
        skeleton_window=Window(10.0, 25.0),
        output_profile=OutputProfile("video", 1920, 1080, None),
    )
    pipeline = SkeletonPipeline(recorder, editor, FakeCaptioner(), FakePublisher(), cfg)

    pipeline.run(make_match(), wait_for_stop=lambda: None)

    (recording, plan, profile, out) = editor.calls[0]
    assert plan.windows == (Window(10.0, 25.0),)
    assert (profile.width, profile.height) == (1920, 1080)
    assert out.parent == tmp_path / "out"


def test_skeleton_publishes_rendered_video_with_caption(tmp_path: Path) -> None:
    recorder = FakeRecorder(tmp_path / "game.mkv")
    editor = FakeEditor()
    captioner = FakeCaptioner(text="Katarina • 18/3/7 • Victory")
    publisher = FakePublisher()
    cfg = make_config(compilations_dir=tmp_path / "out")
    pipeline = SkeletonPipeline(recorder, editor, captioner, publisher, cfg)

    pipeline.run(make_match(), wait_for_stop=lambda: None)

    (video, caption) = publisher.calls[0]
    assert video == editor.calls[0][3]
    assert caption == "Katarina • 18/3/7 • Victory"


def test_skeleton_deletes_transient_recording(tmp_path: Path) -> None:
    recording = tmp_path / "game.mkv"
    recorder = FakeRecorder(recording)
    cfg = make_config(compilations_dir=tmp_path / "out")
    pipeline = SkeletonPipeline(recorder, FakeEditor(), FakeCaptioner(), FakePublisher(), cfg)

    pipeline.run(make_match(), wait_for_stop=lambda: None)

    assert not recording.exists()
