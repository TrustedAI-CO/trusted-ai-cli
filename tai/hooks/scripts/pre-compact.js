#!/usr/bin/env node
/**
 * PreCompact Hook - Save state before context compaction
 *
 * Cross-platform (Windows, macOS, Linux)
 *
 * Runs before Claude compacts context, giving you a chance to
 * preserve important state that might get lost in summarization.
 *
 * Writes a resume note to .context/compact-resume.md so Claude
 * can pick up where it left off after compaction.
 */

const path = require('path');
const {
  getSessionsDir,
  getDateTimeString,
  getTimeString,
  findFiles,
  ensureDir,
  appendFile,
  readFile,
  writeFile,
  runCommand,
  isGitRepo,
  log
} = require('../lib/utils');

const MAX_RESUME_LINES = 50;

function buildResumeNote() {
  const timestamp = getDateTimeString();
  const sections = [`# Compact Resume\n\nSaved at ${timestamp}\n`];

  // Git status: what branch, what's changed
  if (isGitRepo()) {
    const branch = runCommand('git branch --show-current');
    if (branch.success) {
      sections.push(`## Branch\n\n${branch.output}\n`);
    }

    const diffStat = runCommand('git diff --stat HEAD');
    if (diffStat.success && diffStat.output.trim()) {
      const lines = diffStat.output.split('\n').slice(0, 20);
      sections.push(`## Uncommitted Changes\n\n\`\`\`\n${lines.join('\n')}\n\`\`\`\n`);
    }

    const recentLog = runCommand('git log --oneline -5');
    if (recentLog.success && recentLog.output.trim()) {
      sections.push(`## Recent Commits\n\n\`\`\`\n${recentLog.output}\n\`\`\`\n`);
    }
  }

  // Read .context/todos.md if it exists (Conductor workspace todos)
  const todosPath = path.join(process.cwd(), '.context', 'todos.md');
  const todos = readFile(todosPath);
  if (todos && todos.trim() && !todos.includes('[Session context goes here]')) {
    const todoLines = todos.split('\n').slice(0, MAX_RESUME_LINES);
    sections.push(`## Active Tasks\n\n${todoLines.join('\n')}\n`);
  }

  return sections.join('\n');
}

async function main() {
  const sessionsDir = getSessionsDir();
  const compactionLog = path.join(sessionsDir, 'compaction-log.txt');

  ensureDir(sessionsDir);

  // Log compaction event with timestamp
  const timestamp = getDateTimeString();
  appendFile(compactionLog, `[${timestamp}] Context compaction triggered\n`);

  // If there's an active session file, note the compaction
  const sessions = findFiles(sessionsDir, '*-session.tmp');

  if (sessions.length > 0) {
    const activeSession = sessions[0].path;
    const timeStr = getTimeString();
    appendFile(activeSession, `\n---\n**[Compaction occurred at ${timeStr}]** - Context was summarized\n`);
  }

  // Write resume note to .context/compact-resume.md
  const contextDir = path.join(process.cwd(), '.context');
  ensureDir(contextDir);
  const resumePath = path.join(contextDir, 'compact-resume.md');
  const resumeNote = buildResumeNote();
  writeFile(resumePath, resumeNote);

  log('[PreCompact] State saved before compaction');
  log(`[PreCompact] Resume note written to ${resumePath}`);
  process.exit(0);
}

main().catch(err => {
  console.error('[PreCompact] Error:', err.message);
  process.exit(0);
});
