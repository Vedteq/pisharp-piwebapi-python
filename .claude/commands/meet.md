# /meet — SDK Development Meeting

Spawn the **Senior Developer** agent to run the meeting.

**IMPORTANT:** Use the Agent tool NOW with this prompt:

```
You are running an SDK development meeting for the pisharp-piwebapi Python SDK.

Read `CLAUDE.md` for project context and conventions.

## 1. Gather Context

In parallel, read:
- `CLAUDE.md`
- Recent git log (last 10 commits): `git log --oneline -10`
- Pending tasks in `docs/tasks/` (exclude `done/`)
- Check `git status` for uncommitted work

## 2. Assess & Execute

Determine what to work on:
1. **Pending tasks** in `docs/tasks/` (not in `done/`) — execute these first
2. **Uncommitted work** in `git status` — finish and commit it
3. If no tasks, report current SDK status and ask for direction

When executing tasks:
- Follow conventions from `CLAUDE.md` strictly
- Match existing patterns in `src/pisharp_piwebapi/` (read `points.py` and `values.py` as reference)
- Apply PI Web API domain knowledge for accuracy (WebIDs, time strings, batch requests, pagination)
- Write real, working code — no placeholders or stubs

## 3. Verify & Commit

After completing work:
1. Run `pytest` — all tests must pass
2. Run `ruff check src/` — no lint errors
3. Run `mypy src/` — no type errors (fix any introduced by your changes)
4. Commit changes with a clear message
5. Move completed task files to `docs/tasks/done/`

## Guardrails
- Never commit `.env*` files
- Never edit `_generated/` files by hand
- Run tests before committing
- Follow existing code conventions from `CLAUDE.md`
- All public methods need type hints and Google-style docstrings
```
