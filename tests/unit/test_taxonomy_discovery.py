from skill_fleet.taxonomy import discovery


def test_ensure_all_skills_loaded_throttles_recent_scan(tmp_path, monkeypatch):
    skills_root = tmp_path / "skills"
    skill_dir = skills_root / "alpha"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("content", encoding="utf-8")

    metadata_cache: dict[str, object] = {}
    load_calls: list = []

    def fake_loader(skill_path):
        load_calls.append(skill_path)

    previous_scan_state = discovery._last_discovery_scan.copy()
    discovery._last_discovery_scan.clear()

    time_steps = iter([100.0, 100.5])
    monkeypatch.setattr(discovery.time, "monotonic", lambda: next(time_steps))

    try:
        discovery.ensure_all_skills_loaded(skills_root, metadata_cache, fake_loader)
        discovery.ensure_all_skills_loaded(skills_root, metadata_cache, fake_loader)
    finally:
        discovery._last_discovery_scan.clear()
        discovery._last_discovery_scan.update(previous_scan_state)

    assert load_calls == [skill_dir]
