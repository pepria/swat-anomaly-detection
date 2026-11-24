from swatad.rag.retriever import Retriever, load_chunks


def test_knowledge_base_loads_and_tags_are_extracted():
    chunks = load_chunks()
    assert len(chunks) > 20
    assert any("LIT101" in c.tags for c in chunks)


def test_tag_query_returns_tag_chunk():
    r = Retriever()
    hits = r.search("tank level sensor spoofing", tags=["LIT101"], k=5)
    assert len(hits) == 5
    assert any("LIT101" in c.tags for c, _ in hits)
    only = r.search("pump", k=3, sources=["02_tag_dictionary.md"])
    assert all(c.source == "02_tag_dictionary.md" for c, _ in only)
