---
id: matrix
type: matrix
parent: null
children: []
related: []
derived: true
---

> ⚠️ Derived doc — generated/maintained post-ship by an agent; may lag the code. Source of truth is `docs/specs/` + `docs/prd.md`. Regenerate, don't hand-edit as canon.

# Traceability Matrix

| Spec | R-id | Code | Test | Status |
|------|------|------|------|--------|
| SPEC-dashboard-render | R1 | tai/commands/dashboard.py | tests/test_dashboard.py::test_R1_renders_sections | COVERED |
| SPEC-dashboard-render | R2 | tai/commands/dashboard.py | tests/test_dashboard.py::test_R2_pipeline_counts_by_status | COVERED |
| SPEC-dashboard-render | R3 | tai/commands/dashboard.py | tests/test_dashboard.py::test_R3_needs_you_lists_pending | COVERED |
| SPEC-dashboard-render | R4 | tai/commands/dashboard.py | tests/test_dashboard.py::test_R4_coverage_from_matrix | COVERED |
| SPEC-dashboard-render | R5 | tai/commands/dashboard.py | tests/test_dashboard.py::test_R5_recent_from_changelog | COVERED |
| SPEC-dashboard-render | R6 | tai/commands/dashboard.py | tests/test_dashboard.py::test_R6_no_docs_exits_1_with_hint | COVERED |
| SPEC-dashboard-render | R7 | tai/commands/dashboard.py | tests/test_dashboard.py::test_R7_doc_health_flags_issues | COVERED |
| SPEC-dashboard-render | R8 | tai/commands/dashboard.py | tests/test_dashboard.py::test_R8_json_output | COVERED |
| SPEC-dashboard-render | INV1 | tai/commands/dashboard.py | tests/test_dashboard.py::test_INV1_read_only | COVERED |
| SPEC-dashboard-render | INV2 | tai/commands/dashboard.py | tests/test_dashboard.py::test_INV2_malformed_doc_does_not_crash | COVERED |

## Coverage Summary
- Total Behavior rows: 10
- COVERED: 10 (100%)

## Untraced Code
- (none)
