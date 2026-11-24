"""Compare input representations on small, Lean-checked synthetic controls.

Run with the patched engine environment. All measured output stays external.
These controls are not indexed declarations or human relevance judgments.
"""

import argparse
import asyncio
import hashlib
import json
import os
import random
import subprocess
import time
from pathlib import Path

CONTROLS = [
    {
        "id": "addition",
        "query": (
            "Find a theorem stating that addition of natural numbers is commutative."
        ),
        "documents": [
            (
                "original",
                "For natural numbers a and b, a + b equals b + a.",
                "∀ a b : Nat, a + b = b + a",
                "fun a b => Nat.add_comm a b",
                True,
            ),
            (
                "renamed",
                "For natural numbers x and y, x + y equals y + x.",
                "∀ x y : Nat, x + y = y + x",
                "fun x y => Nat.add_comm x y",
                True,
            ),
            (
                "near_miss",
                "For natural numbers a and b, a + b equals a.",
                "∀ a b : Nat, a + b = a",
                "by intro h; exact (by decide : ¬ ((0 : Nat) + 1 = 0)) (h 0 1)",
                False,
            ),
        ],
    },
    {
        "id": "zero",
        "query": (
            "Find a theorem stating that adding zero on the right "
            "preserves a natural number."
        ),
        "documents": [
            (
                "original",
                "For every natural number n, n + 0 equals n.",
                "∀ n : Nat, n + 0 = n",
                "fun n => Nat.add_zero n",
                True,
            ),
            (
                "renamed",
                "For every natural number k, k + 0 equals k.",
                "∀ k : Nat, k + 0 = k",
                "fun k => Nat.add_zero k",
                True,
            ),
            (
                "near_miss",
                "For every natural number n, n + 0 equals zero.",
                "∀ n : Nat, n + 0 = 0",
                "by intro h; exact (by decide : ¬ ((1 : Nat) + 0 = 0)) (h 1)",
                False,
            ),
        ],
    },
]


def digest(value):
    """Fingerprint exact UTF-8 input."""
    return hashlib.sha256(value.encode()).hexdigest()


def render(document, representation):
    """Use a neutral shared name to avoid encoding the expected label."""
    _, description, statement, _, _ = document
    if representation == "description":
        return "probe: " + description
    if representation == "formal":
        return statement
    return "probe: " + description + "\n" + statement


async def run(args):
    """Verify statements and counterexamples before scoring fixed pairs."""
    destination = args.out.resolve()
    if any((p / ".git").exists() for p in (destination, *destination.parents)):
        raise ValueError("Measured outputs must be outside Git checkouts")
    destination.mkdir(parents=True, exist_ok=False)
    (destination / "executed_runner.py").write_bytes(Path(__file__).read_bytes())
    proof = ["import Init", "namespace RepresentationProbe"]
    for control in CONTROLS:
        for name, _, statement, body, valid in control["documents"]:
            proposition = statement if valid else "¬ (" + statement + ")"
            proof.append(f"theorem {control['id']}_{name} : {proposition} := {body}")
    proof.append("end RepresentationProbe")
    source = "\n".join(proof) + "\n"
    source_path = destination / "Controls.lean"
    source_path.write_text(source, encoding="utf-8")
    checked = subprocess.run(
        [str(args.lean), str(source_path)],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    version = subprocess.check_output([str(args.lean), "--version"], text=True).strip()
    (destination / "lean-check.txt").write_text(
        version + "\n" + checked.stdout + checked.stderr, encoding="utf-8"
    )
    if checked.returncode:
        raise RuntimeError("Lean verification failed; no model scores produced")

    os.environ.update(
        OMP_NUM_THREADS="4",
        MKL_NUM_THREADS="4",
        TOKENIZERS_PARALLELISM="false",
        HF_HUB_OFFLINE="1",
        TRANSFORMERS_OFFLINE="1",
    )
    import numpy as np
    import torch

    from lean_explore.util.embedding_client import EmbeddingClient
    from lean_explore.util.reranker_client import RerankerClient

    random.seed(42)
    np.random.seed(42)
    torch.manual_seed(42)
    torch.cuda.manual_seed_all(42)
    models = json.loads(args.models.read_text(encoding="utf-8"))
    embedding = EmbeddingClient(
        models["Qwen/Qwen3-Embedding-0.6B"]["path"], max_length=512, batch_size=32
    )
    reranker = RerankerClient(
        models["Qwen/Qwen3-Reranker-0.6B"]["path"], max_length=256, batch_size=16
    )
    records = []
    started = time.monotonic()
    for control in CONTROLS:
        query = control["query"]
        embedded_query = embedding.model.prompts.get("query", "") + query
        query_tokens = len(embedding.model.tokenizer.encode(embedded_query))
        q = np.array((await embedding.embed([query], is_query=True)).embeddings[0])
        for representation in ("description", "formal", "combined"):
            texts = [render(d, representation) for d in control["documents"]]
            vectors = np.array((await embedding.embed(texts)).embeddings)
            cosine = vectors @ q / (np.linalg.norm(vectors, axis=1) * np.linalg.norm(q))
            scores = (await reranker.rerank(query, texts)).scores
            for document, text, similarity, score in zip(
                control["documents"], texts, cosine.tolist(), scores
            ):
                document_tokens = len(embedding.model.tokenizer.encode(text))
                pair = reranker._format_pair(query, text)
                tokens = len(reranker.tokenizer.encode(pair, add_special_tokens=True))
                records.append(
                    {
                        "control": control["id"],
                        "variant": document[0],
                        "representation": representation,
                        "query": query,
                        "document": text,
                        "query_sha256": digest(query),
                        "document_sha256": digest(text),
                        "reranker_pair_sha256": digest(pair),
                        "tokens": tokens,
                        "embedding_query_sha256": digest(embedded_query),
                        "embedding_query_tokens": query_tokens,
                        "embedding_document_tokens": document_tokens,
                        "embedding_truncated": max(query_tokens, document_tokens) > 512,
                        "truncated": tokens > reranker.max_length,
                        "statement_true": document[4],
                        "embedding_cosine": similarity,
                        "reranker_score": score,
                    }
                )
    output = {
        "scope": (
            "Synthetic formal-consistency diagnostic; no benchmark relevance labels."
        ),
        "lean_version": version,
        "proof_source_sha256": digest(source),
        "lean_exit_code": checked.returncode,
        "models": models,
        "seed": 42,
        "embedding_max_length": 512,
        "reranker_max_length": 256,
        "embedding_query_prompt": embedding.model.prompts.get("query"),
        "embedding_dtype": str(next(embedding.model.parameters()).dtype),
        "reranker_dtype": str(next(reranker.model.parameters()).dtype),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "records": records,
        "scoring_elapsed_seconds": time.monotonic() - started,
        "limits": "Two invented tasks; verification toolchain differs from the corpus. "
        "False statements are deliberate probes, not real declarations. "
        "Do not use these scores as retrieval accuracy or tune on reserved test data.",
    }
    (destination / "scores.json").write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {"pairs": len(records), "truncated": sum(r["truncated"] for r in records)}
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", type=Path, required=True)
    parser.add_argument("--lean", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    asyncio.run(run(parser.parse_args()))
