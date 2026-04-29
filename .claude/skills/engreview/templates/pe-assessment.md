# Principal Engineer Assessment: [Domain]

---

### Architectural Consistency
> Does the proposed solution follow the patterns established in the codebase and ADRs?

| Pattern / Decision | Status | Notes |
|---|---|---|
| [existing pattern or ADR] | Consistent / Contradicts / N/A | [what aligns or conflicts] |

**ADR conflict flag:** Yes — contradicts ADR-XXXX / No conflicts found
> If yes: a new ADR is required before proceeding. State which decision needs to be recorded.

---

### The 7 PE Questions

1. **Failure mode** — What breaks first and how badly does it propagate? What is the blast radius?
2. **Future options** — Does this decision close off future options or keep them open?
3. **Scale** — What does this look like at 10x load or 10x team size? Where does it break?
4. **Operability** — Who operates this at 2am? What do they need to diagnose it? Is that documented?
5. **Coupling** — What hidden dependencies or tight coupling does this introduce?
6. **Compliance** — Does this touch user data, customer records, or any PII/PHI? Has that been flagged?
7. **Technical debt** — Is this the right solution or a workaround? If a workaround, is the root cause documented?

---

### Risk Summary

| Risk | Severity | Recommendation |
|---|---|---|
| [description] | High / Medium / Low | [what to do about it] |

---

### Overall Verdict

**Recommendation:** Approve / Approve with conditions / Reject
**Confidence:** High / Medium / Low
**Conditions (if any):** [what must be true before proceeding]
**ADR required:** Yes / No — [which decision needs recording]

---

### What This Review Did Not Cover
> Blind spots — what would need further investigation before full confidence.

- [limitation or gap in this review]
