from silicon_debug.retrieval import BM25Index
from silicon_debug.schemas import Evidence


def test_bm25_is_ranked_and_bounded():
    docs = [
        Evidence(evidence_id="doc:a", source="doc", text="PCIe completion timeout", provenance="a"),
        Evidence(evidence_id="doc:b", source="doc", text="thermal warning", provenance="b"),
    ]
    hits = BM25Index(docs).search("pcie timeout", top_k=99)
    assert [hit.evidence.evidence_id for hit in hits] == ["doc:a"]

