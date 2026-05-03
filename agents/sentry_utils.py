import sentry_sdk
import yaml

from agents.config import AGENTS_SENTRY_DSN

def confidence_to_numeric(confidence: str) -> int:
    mapping = {"high": 3, "medium": 2, "low": 1}
    return mapping.get(confidence, 0)

def record_agent_run(
    agent_name: str,
    result_yaml: str,
    usage_by_turn: list[dict],
) -> None:
    if not AGENTS_SENTRY_DSN:
        return
    sentry_sdk.init(dsn=AGENTS_SENTRY_DSN, traces_sample_rate=1.0)

    parsed = yaml.safe_load(result_yaml)
    status = parsed.get("metadata", {}).get("status", "partial")
    confidence = parsed.get("metadata", {}).get("confidence", "")

    input_tokens = sum(t["input_tokens"] for t in usage_by_turn)
    output_tokens = sum(t["output_tokens"] for t in usage_by_turn)
    total_tokens = input_tokens + output_tokens

    with sentry_sdk.start_transaction(name="agent.run", sampled=True) as transaction:
        transaction.set_tag("agent", agent_name)
        transaction.set_data("input_tokens", input_tokens)
        transaction.set_data("output_tokens", output_tokens)
        transaction.set_data("total_tokens", total_tokens)
        transaction.set_data("turns_used", len(usage_by_turn))
        transaction.set_data("confidence_numeric", confidence_to_numeric(confidence))

        transaction.status = "ok" if status == "completed" else "deadline_exceeded"
