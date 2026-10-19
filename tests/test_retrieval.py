from continuitybench.generator import generate_cases
from continuitybench.metrics import retrieval_recall_at_k
from continuitybench.retrieval import BM25Retriever, DenseRetriever, HybridRetriever, KeywordRetriever, NoRetrievalBaseline
from continuitybench.schema import build_model_input


def _docs_for_case(case):
    return [turn["content"] for turn in build_model_input(case)["source_conversation"]]


def test_no_retrieval_returns_empty():
    docs = _docs_for_case(generate_cases(1)[0])
    retriever = NoRetrievalBaseline(docs)
    assert retriever.retrieve("any", k=3) == []


def test_retrievers_return_ranked_results():
    case = generate_cases(1, seed=7)[0]
    docs = _docs_for_case(case)

    for retriever_cls in (KeywordRetriever, BM25Retriever, DenseRetriever, HybridRetriever):
        retriever = retriever_cls(docs)
        ranked = retriever.retrieve(case["handoff_task"], k=3)
        assert len(ranked) == 3
        assert ranked[0][2] >= ranked[-1][2]


def test_keyword_recall_is_bounded():
    case = generate_cases(1, seed=7)[0]
    docs = _docs_for_case(case)
    retriever = KeywordRetriever(docs)
    ranked = retriever.retrieve(case["handoff_task"], k=5)
    recall = retrieval_recall_at_k(case["required_facts"], [doc for _, doc, _ in ranked])
    assert 0.0 <= recall <= 1.0
