"""Conservative, deterministic evidence review.

A match means only that the submitted text contains the claim. It is NOT an
independent check of truth, provenance, legal compliance, or product safety.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any

MAX_CLAIMS = 8
MAX_EVIDENCE = 12
MAX_CLAIM_CHARS = 500
MAX_EVIDENCE_CHARS = 12000
MAX_TITLE_CHARS = 160
STOP_WORDS = frozenset({
    "a", "an", "the", "and", "or", "of", "in", "on", "for", "to", "is", "are",
    "was", "were", "it", "with", "this", "that", "has", "have", "had", "by",
    "as", "at", "from", "di", "il", "la", "le", "i", "gli", "un", "una", "e",
    "per", "con", "del", "della", "sono", "ha", "dei", "delle", "ad", "su",
})


class InputError(ValueError):
    """A request violates an input contract."""


def _compact(value: str) -> str:
    return " ".join(value.split())


def _fold(value: str) -> str:
    return _compact(value).casefold()


def _terms(value: str) -> set[str]:
    return {
        term for term in re.findall(r"[^\W_]+", value.casefold(), re.UNICODE)
        if len(term) > 1 and term not in STOP_WORDS and not term.isdecimal()
    }


def _numbers(value: str) -> set[str]:
    return set(re.findall(r"(?<!\w)\d+(?:[.,]\d+)?(?!\w)", value))


def _required_string(value: Any, name: str, max_length: int) -> str:
    if not isinstance(value, str):
        raise InputError(f"{name} must be a string")
    value = _compact(value)
    if not value:
        raise InputError(f"{name} must not be empty")
    if len(value) > max_length:
        raise InputError(f"{name} exceeds {max_length} characters")
    return value


def _optional_url(value: Any) -> str:
    if not value:
        return ""
    if not isinstance(value, str) or len(value) > 500:
        raise InputError("source_url must be a short string")
    if not re.fullmatch(r"https?://[^\s<>\"']+", value):
        raise InputError("source_url must begin with http:// or https://")
    return value


def validate_request(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise InputError("JSON object expected")
    raw_claims = payload.get("claims")
    if not isinstance(raw_claims, list) or not (1 <= len(raw_claims) <= MAX_CLAIMS):
        raise InputError(f"claims must contain 1 to {MAX_CLAIMS} strings")
    claims = [_required_string(x, f"claims[{i}]", MAX_CLAIM_CHARS)
              for i, x in enumerate(raw_claims)]
    raw_evidence = payload.get("evidence")
    if not isinstance(raw_evidence, list) or not (1 <= len(raw_evidence) <= MAX_EVIDENCE):
        raise InputError(f"evidence must contain 1 to {MAX_EVIDENCE} entries")
    items: list[dict[str, str]] = []
    seen: set[str] = set()
    for index, raw in enumerate(raw_evidence):
        if not isinstance(raw, dict):
            raise InputError(f"evidence[{index}] must be an object")
        eid = _required_string(raw.get("id"), "evidence.id", 60)
        if not re.fullmatch(r"[A-Za-z0-9_-]+", eid):
            raise InputError("evidence.id may only use A-Z, a-z, 0-9, _ and -")
        if eid in seen:
            raise InputError("evidence ids must be unique")
        seen.add(eid)
        title = _required_string(raw.get("title"), "evidence.title", MAX_TITLE_CHARS)
        content = _required_string(raw.get("content"), "evidence.content", MAX_EVIDENCE_CHARS)
        url = _optional_url(raw.get("source_url", ""))
        items.append({"id": eid, "title": title, "content": content, "source_url": url})
    return {"claims": claims, "evidence": items}


def _excerpt(text: str, pos: int, needle_len: int, budget: int = 260) -> str:
    start = max(0, pos - 45)
    end = min(len(text), max(start + budget, pos + needle_len + 45))
    return ("..." if start else "") + text[start:end] + ("..." if end < len(text) else "")


def _matching_evidence(claim: str, evidence: dict[str, str]) -> tuple[str, str]:
    full = _fold(evidence["content"])
    phrase = _fold(claim)
    location = full.find(phrase)
    if location >= 0:
        return "SOURCE_TEXT_MATCH", _excerpt(full, location, len(phrase))
    # A numerical discrepancy is only a *flag*. It is never automatically a
    # definitive contradiction, and never treated as supported evidence.
    same_context = len(_terms(claim) & _terms(full)) >= 2
    nums_claim = _numbers(claim)
    nums_source = _numbers(full)
    if same_context and nums_claim and nums_source and nums_claim.isdisjoint(nums_source):
        return "POSSIBLE_NUMERIC_CONFLICT", _excerpt(full, 0, 0)
    return "INSUFFICIENT_EVIDENCE", ""


def verify(payload: Any) -> dict[str, Any]:
    normalized = validate_request(payload)
    digest = hashlib.sha256(json.dumps(
        normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")).hexdigest()
    results = []
    for idx, claim in enumerate(normalized["claims"], start=1):
        matches = []
        conflicts = []
        for item in normalized["evidence"]:
            status, excerpt = _matching_evidence(claim, item)
            citation = {"id": item["id"], "title": item["title"],
                        "source_url": item["source_url"], "excerpt": excerpt}
            if status == "SOURCE_TEXT_MATCH":
                matches.append(citation)
            elif status == "POSSIBLE_NUMERIC_CONFLICT":
                conflicts.append(citation)
        if matches and conflicts:
            verdict = "MIXED_EVIDENCE_REVIEW"
        elif matches:
            verdict = "SOURCE_TEXT_MATCH"
        elif conflicts:
            verdict = "POSSIBLE_NUMERIC_CONFLICT"
        else:
            verdict = "INSUFFICIENT_EVIDENCE"
        results.append({"claim_id": f"C{idx}", "claim": claim, "verdict": verdict,
                        "matches": matches, "possible_conflicts": conflicts,
                        "note": "Text matches do not establish external truth or document authenticity."})
    return {
        "project": "GERVASIO 5.0 EvidenceGate",
        "engine": "deterministic-extractive-v1",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "input_sha256": digest,
        "results": results,
        "caveat": "Only examines user-supplied text; no external-source or legal verification.",
    }
