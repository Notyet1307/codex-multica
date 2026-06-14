#!/usr/bin/env python3
import json
import os
import sys
import urllib.error
import urllib.request


DEFAULT_API_URL = "https://api.deepseek.com/chat/completions"
DEFAULT_MODEL = "deepseek-v4-flash"
REVIEWER_SYSTEM_PROMPT = "You are a pragmatic senior code reviewer. Prioritize correctness, security, data loss, broken CI, and missing validation."


def build_payload(diff_text, prompt_text, model):
    return {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": REVIEWER_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": f"{prompt_text}\n\nReview this PR diff:\n\n```diff\n{diff_text}\n```",
            },
        ],
        "thinking": {"type": "disabled"},
        "stream": False,
    }


def call_deepseek(payload, api_key, api_url):
    request = urllib.request.Request(
        api_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"DeepSeek API request failed: HTTP {error.code}: {detail}")


def extract_review(response):
    try:
        return response["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError) as error:
        raise RuntimeError(f"DeepSeek API response did not include review content: {error}")


def run(diff_path, prompt_path, output_path):
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY is required")

    model = os.environ.get("DEEPSEEK_MODEL", DEFAULT_MODEL)
    api_url = os.environ.get("DEEPSEEK_API_URL", DEFAULT_API_URL)

    with open(diff_path, "r", encoding="utf-8", errors="replace") as file:
        diff_text = file.read()

    with open(prompt_path, "r", encoding="utf-8", errors="replace") as file:
        prompt_text = file.read()

    payload = build_payload(diff_text, prompt_text, model)
    response = call_deepseek(payload, api_key, api_url)
    review = extract_review(response)

    with open(output_path, "w", encoding="utf-8") as file:
        file.write("## DeepSeek PR Review\n\n")
        file.write(review)
        file.write("\n")


def self_test():
    payload = build_payload("diff --git a/file b/file\n+hello\n", "Review carefully.", DEFAULT_MODEL)
    assert payload["model"] == DEFAULT_MODEL
    assert payload["thinking"] == {"type": "disabled"}
    assert payload["stream"] is False
    assert payload["messages"][0]["role"] == "system"
    assert payload["messages"][0]["content"] == REVIEWER_SYSTEM_PROMPT
    assert payload["messages"][1]["role"] == "user"
    assert "Review carefully." in payload["messages"][1]["content"]
    assert "```diff" in payload["messages"][1]["content"]
    assert extract_review({"choices": [{"message": {"content": "Looks good."}}]}) == "Looks good."


def main():
    if len(sys.argv) == 2 and sys.argv[1] == "--self-test":
        self_test()
        return 0

    if len(sys.argv) != 4:
        print(
            "Usage: deepseek_pr_review.py <diff-path> <prompt-path> <output-path>",
            file=sys.stderr,
        )
        return 2

    try:
        run(sys.argv[1], sys.argv[2], sys.argv[3])
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
