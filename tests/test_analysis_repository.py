from pathlib import Path

from storage.repository import AnalysisRepository


def test_analysis_upsert(tmp_path: Path):
    db_url = f"sqlite:///{tmp_path/'db.sqlite'}"
    repo = AnalysisRepository(db_url=db_url)

    p1 = tmp_path / "r1.json"
    p1.write_text("{}")
    first = repo.upsert("com.example.app", str(p1))
    assert first.report_path == str(p1)

    p2 = tmp_path / "r2.json"
    p2.write_text("{}")
    second = repo.upsert("com.example.app", str(p2))
    assert second.id == first.id
    assert second.report_path == str(p2)
