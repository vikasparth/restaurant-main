# Branching Strategy

**Scope:** All engineers and AI agents working in this repository.
**Last updated:** 2026-04-24

---

## Core Rule

**No direct push to `main`.** Every change goes through a feature branch and a Pull Request. `main` is a protected branch — merging requires CI to pass and at least one human approval.

---

## Why This Matters

- **Protects production** — `main` is always in a deployable state
- **CI gets to run** — automated checks catch objective failures before a human has to spot them
- **Creates a reviewable record** — every change has a PR, a description, and a review trail
- **Critical for AI-generated code** — an agent can open many PRs quickly; the branch model ensures each one is independently verified before it can affect `main`

---

## Branch Naming Convention

| Type | Pattern | Example |
|---|---|---|
| New feature | `feature/short-description` | `feature/catering-form` |
| Bug fix | `fix/short-description` | `fix/cart-total-rounding` |
| Chore / tooling | `chore/short-description` | `chore/update-node-version` |
| Documentation | `docs/short-description` | `docs/ci-pipeline-guide` |

Use kebab-case. Keep the branch name short — the PR title and description carry the detail.

---

## Workflow

```mermaid
gitGraph
   commit id: "last release"
   branch feature/catering-form
   checkout feature/catering-form
   commit id: "add form component"
   commit id: "wire up API call"
   commit id: "add validation"
   checkout main
   merge feature/catering-form id: "PR merged ✓"
   branch fix/cart-rounding
   checkout fix/cart-rounding
   commit id: "fix rounding error"
   checkout main
   merge fix/cart-rounding id: "PR merged ✓"
```

**Step by step:**

1. Branch from `main`: `git checkout -b feature/your-task`
2. Make all commits for that task on the branch
3. Push: `git push -u origin feature/your-task`
4. Open a Pull Request targeting `main`
5. CI runs automatically — wait for green
6. Human approves
7. Merge — branch is deleted automatically

---

## Batching Changes — One PR Per Task

A PR represents one complete, self-contained unit of work. Not one commit, not one file — one **task**.

**Correct — batch related commits into one PR:**
```
feature/catering-form
  ├── commit: add CateringForm component
  ├── commit: wire up useCatering hook
  └── commit: add form validation
              ↓
         One PR → CI runs once → one review
```

**Avoid — one PR per commit:**
```
PR #1: add CateringForm component   ← CI runs
PR #2: wire up useCatering hook     ← CI runs again
PR #3: add validation               ← CI runs again
```
Three CI runs, three review cycles, three merge events for one feature. Multiply by an AI agent opening PRs automatically and this becomes significant noise.

---

## Draft PRs — For Work in Progress

Open a **Draft PR** when you want CI feedback before a feature is complete:

- CI runs and gives early feedback
- The merge button is disabled — reviewers know it is not ready
- No approval is wasted on incomplete work
- When complete: click "Ready for review" → final CI run → human reviews → merge

Draft PRs are the right pattern for an AI agent that generates code incrementally and wants validation checkpoints before the feature is done.

---

## Handling Rapid Pushes — Concurrency

Pushing multiple commits quickly to the same branch would trigger a CI run for each push. The CI workflow uses a **concurrency group** to cancel the in-progress run when a new push arrives — only the latest commit gets a full CI run.

Configured in `.github/workflows/ci.yml`:
```yaml
concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true
```

This means: push, push, push → only the last push triggers a complete CI run.

---

## Branch Protection Rules

CI alone does not block merging. **Branch protection rules** configured in GitHub lock the merge button.

**GitHub → Repository Settings → Branches → Add rule for `main`:**

| Rule | Value |
|---|---|
| Require status checks to pass before merging | ✅ On — select the CI job |
| Require at least 1 approval | ✅ On |
| Dismiss stale reviews when new commits are pushed | ✅ On |
| Do not allow bypassing the above settings | ✅ On |
| Allow force pushes | ❌ Off |
| Allow deletions | ❌ Off |

> **Key insight:** A failing CI workflow is *informational* until branch protection is configured. Once configured, it is an *enforcement gate* — no merge without green CI and a human approval.

---

## Note on Future Repo Split

When the frontend and backend move to separate repositories, each team maintains their own copy of this document. The rules are identical; only the CI status check names configured in branch protection will differ per repo.
