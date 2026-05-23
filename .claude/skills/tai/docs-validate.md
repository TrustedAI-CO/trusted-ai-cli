# Docs Validation Reference

This file describes the validation rules for the `docs/` tree. Skills that modify
`docs/` should run these checks before completing.

## Validation Rules

### 1. No Orphans
Every doc in `docs/` must be referenced by at least one other doc (as child or related).
Exception: `REVIEW.md` (type: review) is allowed to be standalone.

### 2. All Links Resolve
Every `parent`, `children`, and `related` ID in frontmatter must point to an
existing doc in the tree. Broken links are errors.

### 3. Bidirectional Links
If doc A lists doc B as a child, doc B must list A as its parent.
Related links don't require bidirectionality (they're cross-references).

### 4. Unique IDs
No two docs may share the same `id` in frontmatter.

### 5. Required Frontmatter
Every `.md` file in `docs/` must have frontmatter with: `id`, `type`, `parent`,
`children`, `related`.

### 6. REQ Coverage (warning, not error)
Every `REQ-*` ID found in `docs/specs/*.md` should have a corresponding row in
`docs/trace/matrix.md`. Missing entries produce warnings, not errors.

### 7. Layer Discipline (advisory)
- `intent.md` should not contain architecture-level detail
- `specs/*.md` should not contain code-level detail (file paths, line numbers)
- `trace/*.md` is the only place that references specific code locations

## How to Validate

### Quick Check (inline in any skill)

After writing docs, run this bash snippet:

```bash
# Check all docs have frontmatter
for f in $(find "$_DOCS_DIR" -name '*.md' -not -path '*/decisions/*'); do
  if ! head -1 "$f" | grep -q '^---$'; then
    echo "MISSING FRONTMATTER: $f"
  fi
done

# Check for orphans — every non-review doc should appear as child or related somewhere
for f in $(find "$_DOCS_DIR" -name '*.md'); do
  _ID=$(grep '^id:' "$f" | head -1 | sed 's/^id: *//')
  _TYPE=$(grep '^type:' "$f" | head -1 | sed 's/^type: *//')
  if [ "$_TYPE" = "review" ]; then continue; fi
  if ! grep -r "$_ID" "$_DOCS_DIR" --include='*.md' -l | grep -v "$f" > /dev/null 2>&1; then
    echo "ORPHAN: $_ID ($f)"
  fi
done
```

### Full Validation

For comprehensive validation, use a Python script. The skill that needs it should
create `docs/validate.py` in the project with these checks:

1. Parse all `.md` files in `docs/` for YAML frontmatter
2. Build a graph of parent/child/related relationships
3. Check rules 1-6 above
4. Report errors (rules 1-5) and warnings (rule 6)
5. Exit 0 if no errors, 1 if errors found

## When to Validate

- `/tai-plan-eng` — after generating specs and plan docs
- `/tai-plan-ceo` — after writing intent.md and decision docs
- `/execute-solo` — after updating trace/matrix.md
- `/docs-init` — after writing trace/ docs
- `/docs-update` — as part of the doc audit
- `/tai-ship` — as a pre-merge gate (warnings only, don't block on REQ coverage)
