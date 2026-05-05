import sentry_sdk

from agents.config import AGENTS_SENTRY_DSN


def confidence_to_numeric(confidence: str) -> int:
    mapping = {"high": 3, "medium": 2, "low": 1}
    return mapping.get(confidence, 0)


def record_agent_run(
    agent_name: str,
    result: dict,
    usage_by_turn: list[dict],  # each dict: {"input_tokens": int, "output_tokens": int}
) -> None:
    if not AGENTS_SENTRY_DSN:
        return
    # why: init on every call is safe — sentry_sdk deduplicates; no global init elsewhere
    sentry_sdk.init(dsn=AGENTS_SENTRY_DSN)

    status = result.get("status", "no_data")
    confidence = result.get("confidence", "")

    input_tokens = sum(t["input_tokens"] for t in usage_by_turn)
    output_tokens = sum(t["output_tokens"] for t in usage_by_turn)
    total_tokens = input_tokens + output_tokens

    # why: capture_event not start_transaction — Performance tab requires a paid Sentry plan;
    # capture_event lands in Issues/Events on all plans and is queryable by tags/extras in dashboards
    sentry_sdk.capture_event({
        "message": f"agent.run: {agent_name}",
        "level": "info",
        "tags": {"agent": agent_name, "status": status},
        "extra": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "turns_used": len(usage_by_turn),
            # why: 0 = "not applicable" for pure Python extractors (no Claude calls, no confidence score)
            "confidence_numeric": confidence_to_numeric(confidence),
        },
    })
