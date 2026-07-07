"""Real adapters wrapping external systems (OBS, FFmpeg, Meta).

These are thin I/O boundaries implementing the ports in ``birdie.ports``. They
are exercised by manual smoke tests, not unit tests — the decision logic they
serve is tested at the pure planner/pipeline seams instead.
"""
