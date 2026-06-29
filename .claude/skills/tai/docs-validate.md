# Docs Validation & Doc-First Conformance Gate

This file describes the validation rules for the `docs/` tree AND the doc-first
conformance gate. Skills that modify `docs/` run the structural checks; `/ship` (and CI)
run the conformance gate. For the layer model, read `docs-philosophy.md`.

## Part A — Structural Validation

### 1. No Orphans
Every doc in `docs/` must be referenced by at least one other doc (as child or related).
Exception: `REVIEW.md` (type: review) is allowed to be standalone.

### 2. All Links Resolve
Every `parent`, `children`, `related`, and `depends_on` ID in frontmatter must point to an
existing doc. Broken links are errors. A spec whose `depends_on` names a deleted/renamed
spec is an **error** — otherwise `/tai-loop` blocks that spec forever as `⛓ blocked` with
no diagnosis that the dependency no longer exists.

### 3. Bidirectional Links
If doc A lists doc B as a child, doc B must list A as its parent. Related links don't
require bidirectionality.

### 4. Unique IDs
No two docs may share the same `id`.

### 5. Required Frontmatter
Every `.md` file in `docs/` must have frontmatter with: `id`, `type`, `parent`,
`children`, `related`. Source-layer docs (`spec`, `decision`) must also have `status`.

### 6. Behavior-Row Coverage (warning)
Every Behavior row ID (`R*`) in `docs/specs/*.md` should have a row in
`docs/matrix.md`. Missing entries produce warnings.

### 7. Layer Discipline (advisory)
- `prd.md` should not contain architecture-level detail
- `specs/*.md` should not contain code-level detail (file paths beyond `code:`/`tests:`, line numbers)
- `matrix.md` is the only place that maps Behavior rows to specific code locations; the
  coarse container→directory map lives in `architecture.md` §4

## Part B — Doc-First Conformance Gate (ENFORCED)

This is what actually stops off-rule behavior. Prose tells the agent the rule; this gate
makes breaking it fail. Run against the PR diff (base…HEAD).

### G1. Approved-spec gate (BLOCK)
For every spec in `docs/specs/`, read its `code:` path and `status:`. If the diff changes
any file under a spec's `code:` path **while that spec is not `status: approved`** → BLOCK.

> No code under a spec's `code:` path may merge until that spec is `status: approved`.

### G2. Source-layer-after-code gate (BLOCK + flag)
In a post-ship / `docs-update` context, if the diff edits any file under `docs/specs/`,
`docs/prd.md`, or `docs/decisions/` → BLOCK and emit a `[CRITICAL]` finding. Source layers
are changed spec-first, never to match shipped code.

### G3. Untraced code (warn)
Files changed under a spec container in `architecture.md` §4 with no matching spec R-id in
the diff → `[INFO] SCOPE CREEP: {file} not traceable to any spec`.

### G4. Behavior-row test coverage (warn)
Each Behavior row ID in a spec touched by the diff should be referenced by a test in the
same diff (`test_R3_*` or `// covers: SPEC-... R3`). Missing → warning.

## How to Validate

### Quick structural check (inline in any skill)

```bash
# Frontmatter present
for f in $(find "$_DOCS_DIR" -name '*.md' -not -path '*/decisions/*'); do
  head -1 "$f" | grep -q '^---$' || echo "MISSING FRONTMATTER: $f"
done

# Orphans — every non-review doc must appear as child or related somewhere
for f in $(find "$_DOCS_DIR" -name '*.md'); do
  _ID=$(grep '^id:' "$f" | head -1 | sed 's/^id: *//')
  _TYPE=$(grep '^type:' "$f" | head -1 | sed 's/^type: *//')
  [ "$_TYPE" = "review" ] && continue
  grep -r "$_ID" "$_DOCS_DIR" --include='*.md' -l | grep -v "$f" > /dev/null 2>&1 \
    || echo "ORPHAN: $_ID ($f)"
done
```

### Doc-first gate G1 (inline, run in /ship and /review)

```bash
# For each spec, block if its code: path is touched while status != approved
_BASE=$(git merge-base HEAD origin/main 2>/dev/null || git merge-base HEAD main)
_CHANGED=$(git diff --name-only "$_BASE"...HEAD)
for spec in "$_DOCS_DIR"/specs/*.md; do
  [ -e "$spec" ] || continue
  case "$spec" in *spec.template.md) continue;; esac
  _STATUS=$(grep '^status:' "$spec" | head -1 | sed 's/^status: *//')
  _CODE=$(grep '^code:' "$spec" | head -1 | sed 's/^code: *//')
  [ -z "$_CODE" ] && continue
  if echo "$_CHANGED" | grep -q "^${_CODE}"; then
    if [ "$_STATUS" != "approved" ] && [ "$_STATUS" != "implemented" ]; then
      echo "BLOCK G1: $(basename "$spec") code path '$_CODE' changed but status=$_STATUS (not approved)"
    fi
  fi
done
```

### Full validation
For comprehensive validation, create `docs/validate.py` in the project: parse all `.md`
frontmatter, build the parent/child/related graph, check A1–A7, run gate G1–G4 against the
diff, report errors (A1–A5, G1, G2) and warnings (A6, A7, G3, G4). Exit 0 if no errors, 1
if errors found.

## When to Validate

| Skill | Runs |
|-------|------|
| `/plan-eng` | A1–A5 after writing specs + plan docs |
| `/plan-ceo`, `/plan-product` | A1–A5 after drafting prd.md + decisions |
| `/tai-execute` | A1–A6 after updating matrix.md; G4 self-check |
| `/docs-init` | A1–A5 after scaffolding |
| `/docs-update` | A1–A7 as part of the audit; **must self-check G2 (never edits source layers)** |
| `/review` | G1–G4 conformance gate against the diff |
| `/ship` | **G1, G2 (BLOCK)** + A1–A6 as pre-merge gate; warnings don't block |
