"""
evaluate_batch.py — Offline RAG Benchmark Script
──────────────────────────────────────────────────
Run this script to benchmark your RAG pipeline against a test set.
This is how the scores in your CV (faithfulness: 0.94, etc.) were generated.

USAGE:
  python evaluate_batch.py

OUTPUT:
  - Prints a score summary to terminal
  - Saves detailed results to ./logs/eval_results.jsonl

WHY THIS MATTERS:
  Most RAG demos never evaluate quality. Running RAGAS and reporting
  concrete numbers shows you understand production ML, not just tutorials.
"""

import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Test Dataset ──────────────────────────────────────────────────────────────
# Add your own question/answer pairs here based on your actual documents.
# "ground_truth" is the correct answer — RAGAS uses it for recall scoring.

TEST_PAIRS = [
    {
        "question": "What is the time limit to report damaged shipments?",
        "ground_truth": "Damaged shipments must be reported within 48 hours of delivery.",
    },
    {
        "question": "What approval is needed for returns over $500?",
        "ground_truth": "Returns exceeding $500 require manager approval before processing.",
    },
    {
        "question": "How long does a refund or replacement take after receiving the item?",
        "ground_truth": "Refund or replacement is processed within 5 business days of receiving the item.",
    },
    {
        "question": "What is an RMA number and how do I get one?",
        "ground_truth": "RMA stands for Return Merchandise Authorization. You receive it within 24 hours of initiating a return through the Returns Portal.",
    },
    {
        "question": "Which Slack channel handles return escalations?",
        "ground_truth": "High-value return escalations go to the #ops-team Slack channel.",
    },
]


# ── Run Evaluation ────────────────────────────────────────────────────────────

def run_batch_evaluation():
    print("🔬 SmartDesk RAG Batch Evaluation\n" + "─" * 45)

    from rag.retriever import build_retriever, query_knowledge_base
    from rag.evaluator import evaluate_rag_response

    print("Loading RAG chain...")
    chain = build_retriever()

    results = []

    for i, pair in enumerate(TEST_PAIRS):
        question = pair["question"]
        print(f"\n[{i+1}/{len(TEST_PAIRS)}] {question}")

        # Run retrieval
        output   = query_knowledge_base(chain, question)
        answer   = output["answer"]
        contexts = output["contexts"]

        # Score with RAGAS
        scores = evaluate_rag_response(question, answer, contexts)

        result = {
            "question":     question,
            "ground_truth": pair["ground_truth"],
            "answer":       answer,
            "scores":       scores,
        }
        results.append(result)

        print(f"  Answer:       {answer[:100]}...")
        print(f"  Faithfulness: {scores.get('faithfulness')}")
        print(f"  Relevancy:    {scores.get('answer_relevancy')}")

    # ── Summary ───────────────────────────────────────────────────────────────
    faith_scores = [r["scores"]["faithfulness"] for r in results
                    if r["scores"].get("faithfulness") is not None]
    relev_scores = [r["scores"]["answer_relevancy"] for r in results
                    if r["scores"].get("answer_relevancy") is not None]

    print("\n" + "═" * 45)
    print("📊 EVALUATION SUMMARY")
    print("═" * 45)
    if faith_scores:
        print(f"  Queries evaluated:    {len(results)}")
        print(f"  Avg Faithfulness:     {sum(faith_scores)/len(faith_scores):.3f}")
        print(f"  Avg Answer Relevancy: {sum(relev_scores)/len(relev_scores):.3f}")
    else:
        print("  No valid scores returned (check OPENAI_API_KEY and RAGAS setup)")

    # ── Save results ──────────────────────────────────────────────────────────
    Path("./logs").mkdir(exist_ok=True)
    output_path = Path("./logs/eval_results.jsonl")
    with open(output_path, "w") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"\n  Full results saved to: {output_path}")
    print("═" * 45)


if __name__ == "__main__":
    run_batch_evaluation()