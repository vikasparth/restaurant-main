# Project Rules — Restaurant Management System

## Workspace Scope
- You MUST operate ONLY inside the `main_project` directory.
- Never modify files inside ../lovable_project.
- Treat ../lovable_project as READ-ONLY reference.

## Migration Rules
When asked to migrate UI:

1. ONLY analyze files changed in the latest commit of ../lovable_project.
2. DO NOT scan entire repository history.
3. DO NOT re-copy unchanged files.
4. Copy only newly added or modified components.
5. Preserve UI exactly:
   - no style changes
   - no layout changes
   - no theme changes
   - no renaming visual classes

## Performance Rules (Token Saving)
- Never read entire folders unless explicitly requested.
- Prefer git diff to detect changes.
- Avoid opening large files unnecessarily.
- Work file-by-file.

## Code Quality Rules
- No file > 500 lines.
- Split logic into modules.
- Separate UI, services, routes, and models.
- Follow scalable folder architecture.

## Backend Expectations
- Backend lives only in main_project.
- Add authentication, APIs, and database layers here.
- Do not generate backend code inside lovable_project.

## Migration Command Behavior
When user says:
"Migrate latest Lovable changes"

You MUST:
1. Run git diff against latest lovable_project commit.
2. Identify changed files only.
3. Migrate incrementally.
4. Confirm migrated file list before proceeding.