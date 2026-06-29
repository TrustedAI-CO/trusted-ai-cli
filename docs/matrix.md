---
id: matrix
type: matrix
parent: null
children: []
related: []
derived: true
---

> ⚠️ Derived doc — maintained live by an agent as code changes; may still lag. Source of truth is `docs/specs/` + `docs/prd.md`. Regenerate, don't hand-edit as canon.

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
| SPEC-dashboard-serve | R1 | tai/commands/dashboard.py | tests/test_dashboard_serve.py::test_R1_binds_and_serves_page | COVERED |
| SPEC-dashboard-serve | R2 | tai/commands/dashboard.py | tests/test_dashboard_serve.py::test_R2_api_matches_cli_json | COVERED |
| SPEC-dashboard-serve | R3 | tai/commands/dashboard.py | tests/test_dashboard_serve.py::test_R3_page_has_all_sections | COVERED |
| SPEC-dashboard-serve | R4 | tai/commands/dashboard.py | tests/test_dashboard_serve.py::test_R4_api_reflects_live_changes | COVERED |
| SPEC-dashboard-serve | R5 | tai/commands/dashboard.py | tests/test_dashboard_serve.py::test_R5_binds_requested_port | COVERED |
| SPEC-dashboard-serve | R6 | tai/commands/dashboard.py | tests/test_dashboard_serve.py::test_R6_port_in_use_raises | COVERED |
| SPEC-dashboard-serve | R7 | tai/commands/dashboard.py | tests/test_dashboard_serve.py::test_R7_no_docs_exits_1 | COVERED |
| SPEC-dashboard-serve | R8 | tai/commands/dashboard.py | tests/test_dashboard_serve.py::test_R8_clean_shutdown | COVERED |
| SPEC-dashboard-serve | R9 | tai/commands/dashboard.py | tests/test_dashboard_serve.py::test_R9_default_bind_is_loopback | COVERED |
| SPEC-dashboard-serve | INV2 | tai/commands/dashboard.py | tests/test_dashboard_serve.py::test_R2_api_matches_cli_json | COVERED |
| SPEC-dashboard-serve | INV3 | tai/commands/dashboard.py | tests/test_dashboard_serve.py::test_R9_default_bind_is_loopback | COVERED |

## Coverage Summary
- Total Behavior rows: 21
- COVERED: 21 (100%)

## Untraced Code
- (none)
