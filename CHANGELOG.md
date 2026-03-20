# CHANGELOG


## [0.4.1.2] - 2026-03-20

### Changed

- **skills**: Rename plan-ceo/plan-ceo-light to plan-biz/plan-biz-light across all skill definitions, cross-references, README, and CHANGELOG


## v0.7.0 (2026-03-20)

### Chores

- Bump version and changelog (v0.4.1.1)
  ([`38bc125`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/38bc125afc334f4516835fbd8b08894c012d2c57))

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>


## v0.6.0 (2026-03-20)

### Chores

- Bump version and changelog (v0.4.1.0)
  ([`e322684`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/e3226841543e5d955922ad94597bac8a86cee9a0))

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>

### Features

- **pdf**: Extract single H1 as title for all templates and persist to file
  ([`4b7df90`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/4b7df90d107790ff206c31bac15e4755e8c47908))

H1 → title promotion was article-only. Now works for report, slides, and any future template. When
  an H1 is extracted, the title is written back to the source file's frontmatter so subsequent runs
  don't re-prompt.


## v0.5.4 (2026-03-20)

### Chores

- Resolve merge conflict in CHANGELOG.md (main → develop)
  ([`6f17b35`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/6f17b3505ae4dfd98cbf00559987381b4dda48d2))

### Continuous Integration

- Add style to semantic-release allowed and patch tags
  ([`aa7c9b9`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/aa7c9b9b2e341e8a70fa0a61548d274d75cf15ef))

### Features

- **pdf**: Auto-extract single H1 as article title and prompt for missing frontmatter
  ([`38202e5`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/38202e522ab026d34655788ab27248576b858e79))

For article template, when exactly one H1 heading exists in the markdown: - Extract it as the
  document title (used by template title block) - Remove the H1 from body content - Promote all
  remaining headings by one level (## → #, ### → ##)

When required frontmatter fields are missing (title/author for article/report): - Prompt the user
  interactively - Write the frontmatter back to the source file - Warn in non-interactive mode


## v0.5.3 (2026-03-20)

### Bug Fixes

- **skills**: Resolve skill discovery for pip/uv-tool installs
  ([`9a5b871`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/9a5b87144a4863463d4cebdb42dcf36c832c3a64))

Same issue as templates — skills weren't findable outside the repo. Add __file__-relative path
  lookup and include .claude/skills/tai in the wheel as tai/data/skills via force-include.

### Chores

- Bump version and changelog (v0.4.0.1)
  ([`92752de`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/92752def403b27da55387ece7a15aaf74982827f))

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>

### Code Style

- **templates**: Update article and report Typst templates
  ([`b9288b9`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/b9288b925d3a92e720a4d801f028a3d5146a57e0))

Article: add heading numbering (1.1.), figure captions, revert to no page header with single-number
  page numbering. Both: hide thematic breaks (---) from rendering in PDF output.


## v0.5.2 (2026-03-20)

### Bug Fixes

- **pdf**: Resolve template discovery and add setup-templates to post-update
  ([`0b94d86`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/0b94d86a4fc99089f811f9602c624fcabf35285a))

Template discovery failed when running tai from outside the repo because it relied on importlib or
  git-root lookups. Add __file__-relative path resolution and include tai/templates/typst in the
  wheel build.

Also wire setup-templates into post-update and post-setup flows so templates are refreshed alongside
  skills and hooks.


## v0.5.1 (2026-03-20)

### Bug Fixes

- **pdf**: Remove unused logo argument from template() call
  ([`83264da`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/83264da9a34bb646e3d0e2b109d3b8feedb892d1))

Templates don't accept a `logo` parameter — the logo is accessed directly from brand assets via
  theme.typ. Passing it caused "unexpected argument: logo" compilation errors.


## v0.5.0 (2026-03-20)

### Chores

- Bump version to v0.4.0 and update changelog
  ([`2c5dcc4`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/2c5dcc46f63307faebc6d85e930c05fec99be3fd))

Add comprehensive changelog entry for the Typst PDF template system.


## v0.4.0 (2026-03-20)

### Chores

- Resolve merge conflict in CHANGELOG.md (develop → main)
  ([`463c0df`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/463c0df3d1c725d05eff92b5a442dde7a9f98671))


## v0.3.1 (2026-03-19)

### Chores

- Bump version and changelog (v0.3.1)
  ([`e828fa8`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/e828fa8747841ef55e13d9914a920ba7ce61e412))

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>

### Documentation

- Remove unnecessary --python 3.11 from uv install command
  ([`65e3abc`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/65e3abc1338df65ff4d5a711b4502d7d6dd316a1))

The project requires Python >=3.11, so pinning to 3.11 is overly restrictive. Let uv pick the best
  available compatible Python.

### Features

- **pdf**: Add template picker and tai pdf templates command
  ([`c68536b`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/c68536b6b99a401ab22f309fd3280b1c097a0379))

Interactive template selection when --template is omitted on .md files. Non-interactive terminals
  get an error with available template names. New 'tai pdf templates' subcommand lists installed
  templates.


## v0.3.0 (2026-03-19)

### Features

- **pdf**: Add Typst-based PDF generation
  ([#26](https://github.com/TrustedAI-CO/trusted-ai-cli/pull/26),
  [`5111d93`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/5111d93b69c9d1cf8fd4e545df8e31b6fb86e0a0))

* feat(pdf): add Typst binary detection, version check, and template system

Core infrastructure for PDF generation: - TypstError hierarchy in errors.py (TypstNotFoundError,
  TypstVersionError, TypstCompileError, TemplateError) - typst.py: find binary, parse version,
  compile documents with timeout handling - templates.py: discover, parse typst.toml, install/remove
  templates with path traversal validation - Bundled Typst templates (proposal, report) and brand
  assets in tai/data/

* feat(pdf): add tai pdf compile command and setup-templates CLI

- pdf.py: setup-templates (install/list/remove) and compile (md/typ → PDF) - Markdown → Typst
  wrapper with cmarker package for native MD rendering - Brand injection (company name, logo,
  colors) with string escaping - Register pdf command group in main.py - Add packaging dependency
  and data force-include in pyproject.toml - Claude Code skill for agent-friendly PDF generation

* chore: bump version and changelog (v0.2.9)

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>

---------

Co-authored-by: Claude Opus 4.6 <noreply@anthropic.com>


## v0.2.1 (2026-03-19)

### Bug Fixes

- **templates**: Correct author name in examples
  ([`5dcba98`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/5dcba98de166cb7489697691e4d5af7c25c4c28f))

- **updater**: Detect uv tool installs and use correct update command
  ([#27](https://github.com/TrustedAI-CO/trusted-ai-cli/pull/27),
  [`a880182`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/a880182b99e5d58c822df98531421df05a327a2d))

`uv pip install` installs to system site-packages but doesn't update the `tai` binary in
  ~/.local/bin/ which is managed by uv tool's isolated venv. This caused ModuleNotFoundError when
  running `tai` after installing via `uv pip install`. Add UV_TOOL installer detection for paths
  under ~/.local/share/uv/tools/ and use `uv tool install --force` for updates. Also fix README
  install instructions to use `uv tool install`.

### Chores

- Resolve merge conflict in CHANGELOG.md
  ([`d27ebd5`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/d27ebd5bc61a8245bb3c01f5f7dd82b2c8321b2b))

- **templates**: Align example naming and add report-example.md
  ([`d419df0`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/d419df07caa817a23448a5a40439fbb886f4d338))

Rename examples to consistent {type}-example.{ext} pattern. Add report-example.md with frontmatter
  for markdown-to-report testing. Remove letter-example.typ (renamed to article-example.typ).

### Documentation

- Update install instructions and mark upcoming features
  ([`197b0e0`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/197b0e0cc17dbcc1f06240ae1c87b5a00ff52806))

Fix install commands to use git+https source since the package is not yet on PyPI. Mark tai ai, tai
  api, and tai secret as coming soon.

### Features

- Add Typst PDF templates with brand assets
  ([`f2b5aad`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/f2b5aad9f5000f5715fc96c6f99fb08d86ad83eb))

Add article, report, and slides templates for `tai pdf compile` with TrustedAI branding (icon, logo,
  banner). Includes shared theme tokens, markdown frontmatter parsing, and markdown-to-slides
  support with `---` as slide separator.

- **article**: Add logo above title, rename letter.typ to article.typ
  ([`3afa9de`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/3afa9de1d027b8cb47d3247e4027dc5989c6a69b))

Add logo on first page above the title block. Rename letter.typ to article.typ for clarity. Remove
  unused icon/banner parameters, use single logo asset with default path to brand/logo.png.

- **pdf**: Add core modules for Typst binary detection and template management
  ([`d0cf7f5`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/d0cf7f58a9d6b490684a80302f20c063be66f2b4))

- tai/core/typst.py: find binary, check version, compile documents - tai/core/templates.py:
  discover, install, validate, remove templates - tai/core/errors.py: add TypstError, TemplateError
  hierarchies - tai/commands/pdf.py: fix .typ root path, document escape function - tai/main.py:
  register pdf command group - tests: 50 new tests for typst, templates, and pdf command

### Refactoring

- **slides**: Fix heading hierarchy, simplify footer, embed logo
  ([`210a5c4`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/210a5c4847cac81415fa1b95ef9785128c817752))

Heading sizes now properly cascade: h1 22pt > h2 20pt > h3 17pt > body 18pt. Simplified footer to
  page number only (removed logo and text). Title slide shows logo above title. Cleaned up redundant
  parameters (icon, banner, footer-logo). Markdown heading extraction uses proper regex for slide
  title parsing.

- **templates**: Unify metadata, brand assets, and code styling
  ([`f304cd3`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/f304cd3791c508cc0b5d0042d6dbdcf9617bd421))

Standardize metadata across all templates to: title, subtitle, author, organization, date, version.
  Remove per-template params (logo, show-page-numbers, institution, affiliation, extra,
  footer-text).

Embed logo (brand/logo.png) directly in templates — no longer passed as a parameter. Remove unused
  banner.png and icon.png assets. Update logo to current brand.

Shared code styling via _code-inline/_code-block in theme.typ: light background with subtle border,
  consistent across article, report, and slides. Fix tag() baseline alignment with outset.

Report: remove decorative circles, add logo on cover, show author in

header. Slides: right-align page number, remove footer text/logo. Consistent author · organization /
  date · version layout everywhere.

Remove test-md-*.typ wrapper files (not needed for testing).


## v0.2.0 (2026-03-19)

### Bug Fixes

- **auth**: Handle session expiry gracefully with auto-retry
  ([`52549ba`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/52549ba13c556c982c3876da840d09b4a0c18abf))

- Widen proactive refresh window from 60s to 300s - Catch network errors in _refresh() with
  user-friendly message - Add _BearerAuth httpx.Auth subclass for transparent 401 retry - Skip 401
  in _raise_on_error (auth flow handles it) - Raise AuthExpiredError on double-401 after retry - Add
  global TaiError catch-all in cli() entry point - Change entry point from app to cli wrapper

### Chores

- Bump version and changelog (v0.2.8)
  ([`2ff5e8b`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/2ff5e8baae5cca3e8455e9459ddb87470a9cab77))

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>

- Bump version and changelog (v0.2.8)
  ([`d55c05a`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/d55c05af9b5c963cc839c9d8c65de80aa11ac6e5))

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>

### Documentation

- Fix install instructions to use git+https source
  ([`4941326`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/4941326349ef2a5a5c0d8e3be86f6c5113167a70))

Package is not published to PyPI. Updated README to show the correct install command from the GitHub
  repository.

- Update project documentation for v0.2.7
  ([`c544b6c`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/c544b6cfd3cf24e80a265b082b836c6b0d618082))

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>

### Refactoring

- **cli**: Remove tai claude compact-status command
  ([`e99d845`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/e99d8456dddc2488d2b5271fd9ad14efd6972e23))

Removes the compact-status command, its helper functions, tests, and all references across docs and
  skills.


## v0.1.2 (2026-03-19)

### Bug Fixes

- **ci**: Use sudo to clean dist/ created by semantic-release container
  ([`32c55ba`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/32c55ba64b06cf6dd6ed3e21a8a09a929393e2d0))

The semantic-release action builds wheels internally with different permissions, making the files
  undeletable by the runner user.


## v0.1.1 (2026-03-19)

### Bug Fixes

- **ci**: Clean dist/ before wheel build and fix uv cache param
  ([`530ffb6`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/530ffb695704f025d13b1ca0d34f91cb390cb2eb))

semantic-release may leave artifacts in dist/ that cause permission errors when uv build --wheel
  runs. Also fix enable-caching → enable-cache for astral-sh/setup-uv.


## v0.1.0 (2026-03-19)

### Bug Fixes

- Add --json as local flag on each command for natural subcommand usage
  ([`b93b4e7`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/b93b4e7f844e67fa0f2f76da6708e8501625a248))

- Remove unused questionary import and dependency
  ([`7e039f2`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/7e039f210017ab67d2254698d6b9daacfabb765b))

- **ci**: Use python -m build in semantic-release container
  ([`dc4795e`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/dc4795ebcd666bd1439d1384605e89b6841070c2))

The semantic-release GitHub Action runs inside a Docker container where uv is not available (exit
  code 127). Switch build_command to use the standard python build module which is available in all
  Python environments.

- **keystore**: Catch all KeyringError subtypes on macOS
  ([#11](https://github.com/TrustedAI-CO/trusted-ai-cli/pull/11),
  [`24bcd2f`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/24bcd2f13383398d49226627adc19a6109d52c32))

* fix(keystore): catch all KeyringError subtypes in store and retrieve

macOS Keychain can return error -25244 (PasswordSetError) which was not caught, crashing `tai
  login`. Broadened exception handling from NoKeyringError to the base KeyringError class so all
  keychain failures gracefully fall back to file storage.

* chore: bump version and changelog (v0.2.4)

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>

---------

Co-authored-by: Claude Opus 4.6 <noreply@anthropic.com>

### Chores

- Bump version and changelog (v0.1.1)
  ([`fabeba3`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/fabeba3e3d7bf43bae3741e7dca303f99b58d9e3))

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>

- Bump version and changelog (v0.2.0)
  ([`ba67a96`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/ba67a963f06b2bea5a8c938941fdd723e3c45d95))

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>

- Bump version and changelog (v0.2.7)
  ([`c831e5b`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/c831e5bf52e0bfc75d84ff013d74a4ac98d8cb8a))

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>

- Resolve merge conflicts with main
  ([`effdc46`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/effdc46fc8c0b8145162e389ad09cc7f988fa062))

- Update uv.lock with python-semantic-release
  ([`07deed2`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/07deed2bb960cc6b5ffc0e64f8306822d3b7c0fb))

### Continuous Integration

- Add GitHub Actions CI and release workflows with semantic-release
  ([`2b07280`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/2b07280b160b250849dfb4f3d9789462feb4874f))

### Documentation

- Add README, ARCHITECTURE, CONTRIBUTING, CHANGELOG, and VERSION
  ([`77b6f86`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/77b6f864232e556ace13fff3140526609b43f43b))

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>

### Features

- Add --docs flag for LLM-friendly usage reference in Markdown
  ([`3f7a0ab`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/3f7a0ab38d61d05e2e36fc67bad611bced827cd7))

- Initial commit — tai internal CLI
  ([`5b16d3a`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/5b16d3a84de95c8e143ed3b5090f9846d6ae9b6c))

- Google OAuth2 PKCE flow with company domain enforcement (hd claim + JWT validation) -
  Profile-based config (XDG, TOML) with per-profile overrides - System keychain token storage via
  keystore module - Commands: auth (login/logout/whoami), secret (set/get/list/delete/rotate/exec),
  config (get/set/list-profiles), ai, api - Plugin system scaffold - Full test suite (unit +
  integration, 80%+ coverage)

- **claude**: Add tai claude login/logout/status commands
  ([`cd2361d`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/cd2361ddb71703b5e66b70167d853f595c7fee4e))

Wraps `claude auth login` subprocess, captures the OAuth URL from stdout and displays it cleanly so
  users (or admins) can open it in any browser. Stdin is forwarded so the user can paste the code
  back directly. logout and status delegate to claude auth logout/status.

- **claude**: Implement PKCE OAuth login flow
  ([`cb33a68`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/cb33a68e868ee0cd36ba98749e3019a93edb15f2))

Replace PTY-wrapped Ink TUI approach with a self-contained PKCE OAuth flow in Python: - Generate
  code_verifier + code_challenge (S256) + state (32 bytes) - Display authorization URL; user visits
  it in any browser - User pastes the full callback URL (or bare code) after authorizing - Exchange
  the code via platform.claude.com/v1/oauth/token - Pass the refresh token to `claude auth login`
  via CLAUDE_CODE_OAUTH_REFRESH_TOKEN so Claude handles profile fetch, API-key creation, and
  credential storage

Eliminates the Ink TUI interaction problem where the paste-code input was gated behind a 3-second
  React state timer and raw-mode PTY forwarding that made input unreliable.

- **cli**: Add tai claude compact-status command
  ([`fe753fd`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/fe753fd2f02258de4d1bd4b1d4e8466cf475747d))

Show session tool-call count, compaction history, and suggestions for when to run /compact. Supports
  --json for scripting. Scans /tmp for counter files by mtime so it works outside the active session
  context.

- **cli**: Add tai claude setup-hooks command
  ([`0105e1d`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/0105e1d3fe08d8ca37ecf0492b137f948064c4e3))

Install curated Claude Code hooks from ECC into ~/.claude/settings.json. Supports --list (preview),
  --remove (uninstall), and --json (scripting). Hooks are tagged with [tai] prefix for ownership
  tracking and idempotent merge with user's custom hooks.

Includes 12 hooks across 6 event types (PreToolUse, PostToolUse, PreCompact, SessionStart, Stop,
  SessionEnd), bundled JS scripts and libraries, and comprehensive test coverage.

- **cli**: Add tai setup interactive config wizard
  ([#12](https://github.com/TrustedAI-CO/trusted-ai-cli/pull/12),
  [`fb108eb`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/fb108eb0abdc4d3c3bc88baed89cb5cb535f3c08))

* feat(cli): add tai setup interactive config wizard

Prompts for every ProfileConfig variable with current values as defaults. Press Enter to skip/keep,
  type a new value to update. Sensitive fields (secret, password, token) are masked. Type coercion
  for int/float/bool. Guards against non-interactive terminals.

* chore: bump version and changelog (v0.2.5)

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>

---------

Co-authored-by: Claude Opus 4.6 <noreply@anthropic.com>

- **cli**: Add tai update command for self-updating from GitHub Releases
  ([`81a2768`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/81a2768a2e4870263c6fa686dd7c05e05badd230))

Auto-detects installer (uv/pipx/pip), streams wheel download with size verification, and refreshes
  skills+hooks post-update. Includes --check flag for dry-run and startup update banner with 24h
  cache.

- **cli**: Agent-friendly improvements — JSON output, TTY detection, quiet mode, exit codes
  ([`5594545`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/5594545e3975619efe9a2d891b09f8f954265d96))

- ExitCode constants (NOT_FOUND=3, PERMISSION_DENIED=4, CONFLICT=5) - ApiError maps HTTP status to
  granular exit codes - is_interactive() helper guards fuzzy pickers from non-TTY contexts - tai
  tasks/meetings: --json outputs structured JSON to stdout - tai tasks/meetings: -q/--quiet outputs
  bare names for piping - tai tasks done: non-interactive without ID exits with USAGE (2) - tai
  meetings: non-interactive fallback prints plain list to stdout - tai project link: guards picker
  with TTY check, clear error for agents - tai project status: --json outputs project data as JSON

- **hooks**: Add resume note to pre-compact hook
  ([`f412b22`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/f412b22d42130bd01e303e0906c401c572a4bccf))

Before compaction, save git branch, uncommitted changes, recent commits, and active tasks to
  .context/compact-resume.md so Claude can pick up where it left off after context summarization.

- **meetings**: Fuzzy picker UI with full searchable pool
  ([`505f58e`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/505f58eefc974db33bb5aaeeaa7a020bfb918023))

- search_select now passes all items to InquirerPy (no pool cap) - max_height=10 limits visible rows
  while keeping all items searchable - meetings default: picker → open Notion; remove static table +
  open subcommand

- **project**: Add tai project commands (link, status, set)
  ([`8aa8f0d`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/8aa8f0d13ad11b5128ac8f9303548a5a57a7c09b))

- **project**: Interactive link picker and new project creation
  ([`a2b06f2`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/a2b06f2b08043e23b2f23baaf009b66275e33e5c))

- **project**: Table-formatted fuzzy picker with client column, InquirerPy fuzzy search
  ([`3047aa6`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/3047aa69297388fd9dcc1cb21dff8f4811b2d3fa))

- **prompt**: Reusable search_select with fuzzy filtering and max 10 results
  ([`b5eccbb`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/b5eccbb403f25e877531764f20483cb7b9c5648e))

- **skills**: Add content-writer skill ([#6](https://github.com/TrustedAI-CO/trusted-ai-cli/pull/6),
  [`9339366`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/93393664a6c2dd5acf5ecdcfab53f31959b75cd7))

* feat(skills): add content-writer skill with voice profiles, slop detection, and templates

Interactive content creation workflow supporting 7 content types (blog, tutorial, release
  announcement, case study, comparison, how-to, changelog). Includes voice profile system for
  consistent tone, AI-slop detection with ~60 patterns across 9 categories, codebase-aware technical
  writing, git-aware release announcements, and 6 structured templates.

* chore: bump version and changelog (v0.1.2)

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>

---------

Co-authored-by: Claude Opus 4.6 <noreply@anthropic.com>

- **skills**: Add light versions of plan-biz, plan-eng, and review skills
  ([`39a0efa`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/39a0efa018e397b984c476dc3fd680a229c0c155))

Speed-optimized variants that trade thoroughness for fast feedback: - plan-biz-light: premise
  challenge + dream state + top 3 risks (no 10-section walkthrough) - plan-eng-light: scope
  challenge + architecture diagram + top concerns (no interactive stops) - review-light:
  CRITICAL-only single-pass review (SQL, race conditions, LLM trust, enums)

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>

- **skills**: Add market-research skill for startup competitive analysis, sizing, and validation
  ([`ee64c98`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/ee64c98f43465e0ebb07ed8ec96879c378515f99))

Bundled Claude Code skill with 3 research modes: - Competitor analysis (SWOT, competitive matrix,
  positioning gaps) - Market sizing (TAM/SAM/SOM, top-down + bottom-up) - Idea validation (demand
  signals, go/no-go assessment)

Includes mandatory web search integration and quality gates.

- **skills**: Add multilingual language policy to all TAI skills
  ([#8](https://github.com/TrustedAI-CO/trusted-ai-cli/pull/8),
  [`14afe49`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/14afe49834a17ec49573534792bc4357129c64ef))

* feat(skills): add multilingual language policy to all TAI skills

Add a Language section to all 15 SKILL.md files instructing Claude to respond in the user's
  conversational language (Japanese, Vietnamese, etc.) while keeping severity labels, verdict
  strings, section headers, and technical terms in English for greppability and consistency.

* chore: bump version and changelog (v0.2.1)

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>

---------

Co-authored-by: Claude Opus 4.6 <noreply@anthropic.com>

- **skills**: Add strategic compact skill for Claude Code
  ([`7bb7e28`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/7bb7e28824697211674417cc9219192257f3bb0c))

tai-workflow-aware compaction guide that teaches Claude when and how to compact based on phase
  transitions (/plan-biz → /plan-eng → implement → /review → /ship). Documents what survives
  compaction, hook behavior, and best practices.

- **skills**: Add tai skills setup/update commands with bundled Claude Code skills
  ([`ee425ad`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/ee425adfe00f336006c95ed9a0a79eaf86c5cb9b))

Add 11 Claude Code skills (review, ship, qa, design-review, etc.) bundled in .claude/skills/tai/ and
  installable to ~/.claude/skills/tai-<name>/ via `tai skills setup` and `tai skills update`.

Skills are discovered as personal Claude Code skills with tai- prefix (e.g. tai-review, tai-ship)
  and include [TAI] in descriptions.

- **skills**: Add tai-project skill for CLI project management
  ([#15](https://github.com/TrustedAI-CO/trusted-ai-cli/pull/15),
  [`3378a8f`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/3378a8f706408690bd1787dbeed23486a999a85a))

* refactor(hooks): extract shared counter file path helper

Move the counter file path convention (claude-tool-count-{sessionId}) into a shared
  getCounterFilePath() utility in hooks/lib/utils.js. Keeps suggest-compact.js and the Python
  compact-status command in sync.

* feat(hooks): add resume note to pre-compact hook

Before compaction, save git branch, uncommitted changes, recent commits, and active tasks to
  .context/compact-resume.md so Claude can pick up where it left off after context summarization.

* feat(cli): add tai claude compact-status command

Show session tool-call count, compaction history, and suggestions for when to run /compact. Supports
  --json for scripting. Scans /tmp for counter files by mtime so it works outside the active session
  context.

* feat(skills): add strategic compact skill for Claude Code

tai-workflow-aware compaction guide that teaches Claude when and how to compact based on phase
  transitions (/plan-biz → /plan-eng → implement → /review → /ship). Documents what survives
  compaction, hook behavior, and best practices.

* chore: bump version and changelog (v0.1.1)

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>

* feat(skills): add content-writer skill (#6)

* feat(skills): add content-writer skill with voice profiles, slop detection, and templates

Interactive content creation workflow supporting 7 content types (blog, tutorial, release
  announcement, case study, comparison, how-to, changelog). Includes voice profile system for
  consistent tone, AI-slop detection with ~60 patterns across 9 categories, codebase-aware technical
  writing, git-aware release announcements, and 6 structured templates.

* chore: bump version and changelog (v0.1.2)

---------

Co-authored-by: Claude Opus 4.6 <noreply@anthropic.com>

* refactor(skills): rename compact skill to smart-compact (#7)

"compact" implied clearing/wiping context. "smart-compact" better conveys the intent: compacting at
  intelligent workflow boundaries rather than arbitrarily.

* feat(skills): add visualization support to content-writer (#9)

* feat(skills): add market-research skill for startup competitive analysis, sizing, and validation

Bundled Claude Code skill with 3 research modes: - Competitor analysis (SWOT, competitive matrix,
  positioning gaps) - Market sizing (TAM/SAM/SOM, top-down + bottom-up) - Idea validation (demand
  signals, go/no-go assessment)

Includes mandatory web search integration and quality gates.

* chore: bump version and changelog (v0.2.0)

* feat(skills): add multilingual language policy to all TAI skills (#8)

* feat(skills): add multilingual language policy to all TAI skills

Add a Language section to all 15 SKILL.md files instructing Claude to respond in the user's
  conversational language (Japanese, Vietnamese, etc.) while keeping severity labels, verdict
  strings, section headers, and technical terms in English for greppability and consistency.

* chore: bump version and changelog (v0.2.1)

* feat(skills): add visualization support to content-writer

Add Mermaid diagram guidance to the content-writer skill: - Step 0E: visualization preference
  briefing question - Step 2: writing rules for diagram inclusion - Step 3D: visualization quality
  gate with opportunity detection - Per-template visualization hints for all 7 templates - New
  references/visualization-guide.md with diagram type matrix

* chore: bump version and changelog (v0.2.2)

* feat(skills): add tech-research skill (#10)

* feat(skills): add tech-research skill

4 research modes: library/tool comparison, architecture decision records, technology deep dives, and
  troubleshooting research. Includes output templates for each mode, research quality checklist, and
  optional context7/chub integration for documentation lookup.

* chore: bump version and changelog (v0.2.3)

* fix(keystore): catch all KeyringError subtypes on macOS (#11)

* fix(keystore): catch all KeyringError subtypes in store and retrieve

macOS Keychain can return error -25244 (PasswordSetError) which was not caught, crashing `tai
  login`. Broadened exception handling from NoKeyringError to the base KeyringError class so all
  keychain failures gracefully fall back to file storage.

* chore: bump version and changelog (v0.2.4)

* feat(cli): add tai setup interactive config wizard (#12)

* feat(cli): add tai setup interactive config wizard

Prompts for every ProfileConfig variable with current values as defaults. Press Enter to skip/keep,
  type a new value to update. Sensitive fields (secret, password, token) are masked. Type coercion
  for int/float/bool. Guards against non-interactive terminals.

* chore: bump version and changelog (v0.2.5)

* feat(skills): add tai-project skill for CLI project management

Teaches Claude Code how to use tai CLI project commands: linking repos to Notion, viewing status,
  managing tasks/meetings, and opening linked tools. Includes non-interactive patterns for agent
  usage.

* chore: bump version and changelog (v0.2.6)

- **skills**: Add tech-research skill
  ([#10](https://github.com/TrustedAI-CO/trusted-ai-cli/pull/10),
  [`6a9670c`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/6a9670c7eb24989979954712ce74dde7afbdd13c))

* feat(skills): add tech-research skill

4 research modes: library/tool comparison, architecture decision records, technology deep dives, and
  troubleshooting research. Includes output templates for each mode, research quality checklist, and
  optional context7/chub integration for documentation lookup.

* chore: bump version and changelog (v0.2.3)

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>

---------

Co-authored-by: Claude Opus 4.6 <noreply@anthropic.com>

- **skills**: Add visualization support to content-writer
  ([#9](https://github.com/TrustedAI-CO/trusted-ai-cli/pull/9),
  [`47ce170`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/47ce17050a1b2be8b0369fe4398a9fcac06f3959))

* feat(skills): add market-research skill for startup competitive analysis, sizing, and validation

Bundled Claude Code skill with 3 research modes: - Competitor analysis (SWOT, competitive matrix,
  positioning gaps) - Market sizing (TAM/SAM/SOM, top-down + bottom-up) - Idea validation (demand
  signals, go/no-go assessment)

Includes mandatory web search integration and quality gates.

* chore: bump version and changelog (v0.2.0)

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>

* feat(skills): add multilingual language policy to all TAI skills (#8)

* feat(skills): add multilingual language policy to all TAI skills

Add a Language section to all 15 SKILL.md files instructing Claude to respond in the user's
  conversational language (Japanese, Vietnamese, etc.) while keeping severity labels, verdict
  strings, section headers, and technical terms in English for greppability and consistency.

* chore: bump version and changelog (v0.2.1)

---------

Co-authored-by: Claude Opus 4.6 <noreply@anthropic.com>

* feat(skills): add visualization support to content-writer

Add Mermaid diagram guidance to the content-writer skill: - Step 0E: visualization preference
  briefing question - Step 2: writing rules for diagram inclusion - Step 3D: visualization quality
  gate with opportunity detection - Per-template visualization hints for all 7 templates - New
  references/visualization-guide.md with diagram type matrix

* chore: bump version and changelog (v0.2.2)

- **skills**: Upgrade market-research to v2.0 with depth framework
  ([#14](https://github.com/TrustedAI-CO/trusted-ai-cli/pull/14),
  [`69e80d1`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/69e80d1cbf8f276d085e9763121fdcec6267a505))

* feat(skills): upgrade market-research to v2.0 with depth framework

Add 10 Market Thinking Frameworks as cognitive patterns (Jobs-to-be-Done, Porter's Five Forces,
  Inversion, Timing, Moat Classification, Blue Ocean, Proxy Skepticism, Willingness-to-Pay,
  Distribution, Second-Order Thinking).

Add interactive research refinement with AskUserQuestion stops, 3-tier depth levels
  (quick/standard/deep), cross-research persistence with staleness detection, and preamble with
  context detection.

Add external templates for competitor analysis, market sizing, idea validation, and investor-ready
  output format. Add market-specific research quality checklist.

* chore: bump version and changelog (v0.2.7)

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>

---------

Co-authored-by: Claude Opus 4.6 <noreply@anthropic.com>

- **skills**: Upgrade tech-research to v2.0 with depth framework
  ([#13](https://github.com/TrustedAI-CO/trusted-ai-cli/pull/13),
  [`bb6bb81`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/bb6bb818308cc987fe175481a396dc1182bcfcb0))

* feat(skills): upgrade tech-research skill to v2.0 with depth framework

Transplant plan-biz's proven depth patterns into tech-research: - Research Prime Directives and
  Thinking Instincts for structured analysis - Depth modes (Quick/Standard/Deep) with user selection
  - Multi-source triangulation protocol for claim verification - Adversarial red team section with
  confidence calibration - Interactive checkpoints for mid-research steering - Forcing questions per
  research mode - Completion summary dashboard - Enhanced templates with red team sections and
  failure modes - Strengthened quality checklist with depth indicators

* chore: bump version and changelog (v0.2.6)

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>

---------

Co-authored-by: Claude Opus 4.6 <noreply@anthropic.com>

- **tasks,meetings**: Add tasks and meetings command groups with filtering
  ([`d00cc4c`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/d00cc4c5bdc22fca350eebd0c3fcfd6b63ff8c2d))

- tai tasks: list, add, done (fuzzy picker) — scoped to linked project - tai meetings: list, add,
  open (with clickable Notion link on ID) — scoped to linked project - -a/--all: show across all
  projects (no .tai.toml required) - -n/--limit: limit number of results - -f/--filter:
  case-insensitive substring filter on name/title - Meetings list sorted by date descending; date
  shown as YYYY-MM-DD only - tai link/unlink/open promoted to top level; tai auth removed
  (login/logout/whoami at top level) - tai set removed — tool bindings managed directly in Notion

### Refactoring

- Replace --docs flag with tai docs subcommand
  ([`0b6a392`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/0b6a392a7abbb047674f56bd032c2e2775f3b8b0))

- **hooks**: Extract shared counter file path helper
  ([`58f96e5`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/58f96e5703224f4812eb749daa71e5776e4c8ed9))

Move the counter file path convention (claude-tool-count-{sessionId}) into a shared
  getCounterFilePath() utility in hooks/lib/utils.js. Keeps suggest-compact.js and the Python
  compact-status command in sync.

- **skills**: Move skills command to tai claude setup-skills
  ([`bbc64fd`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/bbc64fd69665fdf2e7987fba619694aa504692c5))

Consolidate setup/update into a single `tai claude setup-skills` command. Skips existing by default,
  `--force` overwrites. Remove standalone `tai skills` subcommand.

- **skills**: Rename compact skill to smart-compact
  ([#7](https://github.com/TrustedAI-CO/trusted-ai-cli/pull/7),
  [`7fe4285`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/7fe4285b2f859633a3403d81176742774119075c))

"compact" implied clearing/wiping context. "smart-compact" better conveys the intent: compacting at
  intelligent workflow boundaries rather than arbitrarily.

- **skills**: Rename plan-xxx-review to plan-xxx
  ([`bc7c783`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/bc7c783cbe4f471d9391a82f26f902b406544539))

Shorter, cleaner skill names: - plan-biz-review → plan-biz - plan-design-review → plan-design -
  plan-eng-review → plan-eng

Updated all cross-references across skill files.

### Testing

- Fix tests broken by auth top-level promotion and picker pool change
  ([`a1729ef`](https://github.com/TrustedAI-CO/trusted-ai-cli/commit/a1729efe45dc5ef671769c3f27fdd5e10df04bfa))
