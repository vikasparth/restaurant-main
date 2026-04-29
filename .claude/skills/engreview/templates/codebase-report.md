# Codebase Review: [Domain]

**Intent:** [what you are about to build, one sentence]

---

### Existing Entities
| Entity | Key Fields | Location |
|---|---|---|
| [model name] | [field: type, ...] | [file:line] |

### Existing API Endpoints
| Method | Path | Handler | Notes |
|---|---|---|---|
| [GET/POST/...] | [/path] | [function name] | [brief description] |

### Existing State Machines
[List entity state transitions found in service logic — or N/A]

### Test Coverage
| Test File | What Is Covered | Gap |
|---|---|---|
| [file] | [scenarios tested] | [what is missing] |

### Existing Documentation
| Doc | Covers | Status |
|---|---|---|
| [file path] | [what it covers] | Draft / Approved / Missing |

### Reuse Opportunities
> Existing code, components, hooks, or utilities the new feature could reuse rather than rebuild.

| Item | Location | How it could be reused |
|---|---|---|
| [function / component / hook] | [file:line] | [suggested reuse] |

### Potential Conflicts with Intent
| Conflict | Location | Risk | Notes |
|---|---|---|---|
| [description] | [file:line] | High / Medium / Low | [context] |

### Constraints the New Feature Must Respect
- [hard constraint from existing code, schema, or migration]
