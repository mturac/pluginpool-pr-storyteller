# pr-storyteller — examples

Each scenario shows: a starting state, the exact command, the helper's structured output, and what Claude produces as the final PR description.

---

## Scenario 1 — refresh-token rotation feature

**Setup:** A feature branch with two commits beyond `main`:

```
$ git log --oneline main..HEAD
def5678 test(auth): cover stale-token replay
abc1234 feat(auth): rotate refresh tokens
```

**Command:**

```sh
python3 scripts/story.py --base main
```

**Helper output (JSON, faithful to current behaviour):**

```json
{
  "base": "main",
  "head": "HEAD",
  "commits": [
    {"hash": "def5678", "subject": "test(auth): cover stale-token replay"},
    {"hash": "abc1234", "subject": "feat(auth): rotate refresh tokens"}
  ],
  "files_changed": [
    {"path": "src/auth/refresh.py", "additions": 84, "deletions": 12},
    {"path": "tests/test_refresh.py", "additions": 41, "deletions": 0}
  ],
  "suggested_title": "test(auth): cover stale-token replay"
}
```

> Note: `suggested_title` comes from the latest commit subject. Claude is expected to override this — the latest commit was a test, but the *feature* is rotation. See below.

**What Claude does next** (running `/pr-storyteller`):

```markdown
### feat(auth): rotate refresh tokens on every refresh

#### Summary

- Rotate the refresh-token secret on every successful refresh
- Reject any refresh token that has already been redeemed
- Invalidate the full token family on detected replay

#### Changes

- `src/auth/refresh.py` (+84 / −12) — token rotation + replay detection
- `tests/test_refresh.py` (+41 / −0) — coverage for the replay path

#### Test plan

- [ ] Successful login → both access and refresh tokens issued
- [ ] Reuse a refresh token → 401 + token family invalidated
- [ ] Clock-skew tolerance still passes (existing test)
- [ ] Sentry breadcrumbs include the rotation event ID

#### Risk

Medium. Affects every authenticated session. Roll out behind
`AUTH_ROTATE_REFRESH` flag and watch the auth-failure dashboard
for 30 minutes before flipping for the wider population.
```

---

## Scenario 2 — feature branch against `develop` instead of `main`

```sh
python3 scripts/story.py --base develop
```

Works the same way; `--base` controls both the `git log` range and the `git diff --stat` range. If the named branch doesn't exist locally, the helper falls back to `master`.

---

## Scenario 3 — empty diff is safe

When `HEAD` is at the same commit as the base (or you're not in a git repo), the helper emits a structurally valid empty payload and exits zero:

```json
{
  "base": "main",
  "head": "HEAD",
  "commits": [],
  "files_changed": [],
  "suggested_title": null
}
```

The slash command can detect this and prompt the user to either make commits or pick a different base.
