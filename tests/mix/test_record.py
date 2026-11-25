from pathlib import Path

from lean_explore_bench.mix.record import QueryRecord, read_records, write_records


def test_records_round_trip_sorted_by_identifier(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "queries.jsonl"
    assert read_records(path) == []
    records = [
        QueryRecord(
            id=identifier,
            query="∀ a b : ℕ, a + b = b + a",
            query_type="formal",
            variant="statement",
            source="declaration",
            library="core",
            area="Data",
            target="Nat.add_comm",
            judgments={"Nat.add_comm": 3},
            group_id="Nat.add_comm",
            provenance={"method": "language-model"},
        )
        for identifier in ("b", "a")
    ]
    write_records(path, records)
    assert [record.id for record in read_records(path)] == ["a", "b"]
    assert read_records(path)[0] == records[1]
    assert "∀" in path.read_text(encoding="utf-8")
