"""Score dumped pools with Qwen3-Reranker prompted as its model card specifies.

LeanExplore's RerankerClient sends the bare "<Instruct>/<Query>/<Document>" text and
compares the "true" and "false" logits. The model card wraps that text in a chat
prefix and suffix and compares "yes" and "no". This script uses the model card's
format, with LeanExplore's instruction, so the two can be compared on the same pools.
"""

import argparse
import json
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

INSTRUCTION = "Find relevant Lean 4 math declarations"  # LeanExplore's instruction
PREFIX = (
    "<|im_start|>system\nJudge whether the Document meets the requirements based on "
    'the Query and the Instruct provided. Note that the answer can only be "yes" or '
    '"no".<|im_end|>\n<|im_start|>user\n'
)
SUFFIX = "<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"


@torch.no_grad()
def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pools", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--model", default="Qwen/Qwen3-Reranker-0.6B")
    parser.add_argument("--max-length", type=int, default=256,
                        help="token budget for the pair, before prefix and suffix")
    parser.add_argument("--batch-size", type=int, default=50)
    parser.add_argument("--instruction", default=INSTRUCTION)
    args = parser.parse_args()

    tokenizer = AutoTokenizer.from_pretrained(args.model, padding_side="left")
    model = AutoModelForCausalLM.from_pretrained(args.model, dtype=torch.float16)
    model = model.to("cuda").eval()
    yes = tokenizer.convert_tokens_to_ids("yes")
    no = tokenizer.convert_tokens_to_ids("no")
    prefix = tokenizer.encode(PREFIX, add_special_tokens=False)
    suffix = tokenizer.encode(SUFFIX, add_special_tokens=False)

    with Path(args.output).open("x") as out:
        for line in Path(args.pools).read_text().splitlines():
            record = json.loads(line)
            pairs = [
                f"<Instruct>: {args.instruction}\n<Query>: {record['query']}\n"
                f"<Document>: {candidate['document']}"
                for candidate in record["candidates"]
            ]
            scores: list[float] = []
            for start in range(0, len(pairs), args.batch_size):
                encoded = tokenizer(
                    pairs[start : start + args.batch_size],
                    padding=False,
                    truncation=True,
                    max_length=args.max_length,
                    return_attention_mask=False,
                )
                encoded["input_ids"] = [
                    prefix + ids + suffix for ids in encoded["input_ids"]
                ]
                batch = tokenizer.pad(encoded, padding=True, return_tensors="pt")
                logits = model(**batch.to("cuda")).logits[:, -1, :]
                both = torch.stack([logits[:, no], logits[:, yes]], dim=1).float()
                scores += torch.softmax(both, dim=1)[:, 1].tolist()
            out.write(json.dumps({"id": record["id"], "scores": scores}) + "\n")


if __name__ == "__main__":
    main()
