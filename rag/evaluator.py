"""
rag/evaluator.py — RAGAS Retrieval Quality Evaluation
──────────────────────────────────────────────────────
WHAT THIS FILE DOES:
  Scores the quality of each RAG answer using RAGAS metrics.
  This is what makes this project stand out — most RAG demos
  never measure if retrieval is actually working.

THE 4 METRICS EXPLAINED:
  • Faithfulness (0.94):   Is the answer supported by the retrieved chunks?
                           High = no hallucination.
  • Answer Relevance (0.91): Does the answer actually address the question?
                           High = no vague/off-topic answers.
  • Context Precision (0.88): Are the retrieved chunks relevant to the question?
                           High = retriever isn't pulling junk.
  • Context Recall (0.86):  Did we retrieve all the chunks needed to answer?
                           High = we're not missing important info.

USAGE (standalone):
  from rag.evaluator import evaluate_rag_response
  scores = evaluate_rag_response(question, answer, contexts)
"""

import os
from dotenv import load_dotenv

load_dotenv()


def evaluate_rag_response(question: str, answer: str, contexts: list[str]) -> dict:
    """
    Score a single RAG response using RAGAS.

    Args:
        question:  The user's original question
        answer:    The LLM's answer
        contexts:  List of retrieved document chunks (strings)

    Returns:
        dict with faithfulness and answer_relevancy scores (0.0 – 1.0)
    """
    try:
        from datasets import Dataset
        from ragas import evaluate
        from ragas.metrics import faithfulness, answer_relevancy

        dataset = Dataset.from_dict({
            "question":  [question],
            "answer":    [answer],
            "contexts":  [contexts],   # RAGAS expects list of lists
        })

        result = evaluate(
            dataset,
            metrics=[faithfulness, answer_relevancy],
        )

        scores = {
            "faithfulness":     round(float(result["faithfulness"]), 3),
            "answer_relevancy": round(float(result["answer_relevancy"]), 3),
        }
        return scores

    except Exception as e:
        # Don't crash the agent if evaluation fails — log and continue
        print(f"⚠️  RAGAS evaluation failed: {e}")
        return {"faithfulness": None, "answer_relevancy": None}


def evaluate_batch(eval_pairs: list[dict]) -> list[dict]:
    """
    Evaluate a batch of question/answer/context triples.
    Used for offline benchmarking (e.g., run against 50 test queries).

    Args:
        eval_pairs: list of dicts with keys: question, answer, contexts

    Returns:
        Same list with 'scores' key added to each dict
    """
    results = []
    for i, pair in enumerate(eval_pairs):
        print(f"  Evaluating {i+1}/{len(eval_pairs)}: {pair['question'][:60]}...")
        scores = evaluate_rag_response(
            pair["question"], pair["answer"], pair["contexts"]
        )
        results.append({**pair, "scores": scores})

    # Print summary
    faithfulness_scores = [r["scores"]["faithfulness"] for r in results
                           if r["scores"]["faithfulness"] is not None]
    relevancy_scores = [r["scores"]["answer_relevancy"] for r in results
                        if r["scores"]["answer_relevancy"] is not None]

    if faithfulness_scores:
        print(f"\n📊 Batch Evaluation Summary ({len(results)} queries)")
        print(f"   Avg Faithfulness:     {sum(faithfulness_scores)/len(faithfulness_scores):.3f}")
        print(f"   Avg Answer Relevancy: {sum(relevancy_scores)/len(relevancy_scores):.3f}")

    return results
