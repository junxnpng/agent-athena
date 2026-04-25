#!/usr/bin/env node
/**
 * Athena SessionStart hook
 *
 * Loads last work context from .athena/last-context.json
 * and injects it as a session reminder.
 */

import { existsSync, readFileSync, readdirSync } from 'fs';
import { join } from 'path';

function readStdin(timeoutMs = 3000) {
  return new Promise((resolve) => {
    const chunks = [];
    let settled = false;
    const timeout = setTimeout(() => {
      if (!settled) {
        settled = true;
        process.stdin.destroy();
        resolve(Buffer.concat(chunks).toString('utf-8'));
      }
    }, timeoutMs);
    process.stdin.on('data', (chunk) => chunks.push(chunk));
    process.stdin.on('end', () => {
      if (!settled) {
        settled = true;
        clearTimeout(timeout);
        resolve(Buffer.concat(chunks).toString('utf-8'));
      }
    });
    process.stdin.on('error', () => {
      if (!settled) {
        settled = true;
        clearTimeout(timeout);
        resolve('');
      }
    });
  });
}

function readJson(path) {
  try {
    if (!existsSync(path)) return null;
    return JSON.parse(readFileSync(path, 'utf-8'));
  } catch {
    return null;
  }
}

function checkContinuousOvernight(cwd) {
  const baseDir = join(cwd, '.athena', 'continuous');
  if (!existsSync(baseDir)) return null;

  let entries;
  try {
    entries = readdirSync(baseDir, { withFileTypes: true }).filter((d) => d.isDirectory());
  } catch {
    return null;
  }

  const lines = [];
  for (const entry of entries) {
    const stateFile = join(baseDir, entry.name, 'state.json');
    const state = readJson(stateFile);
    if (!state) continue;
    if (!state.active && state.status !== 'blocked') continue;

    const startedAt = state.started_at ? new Date(state.started_at) : null;
    const elapsedH = startedAt ? (Date.now() - startedAt.getTime()) / 3.6e6 : 0;

    let line = `[continuous-overnight] id=${state.id} status=${state.status} iter=${state.iteration ?? 0}/${state.max_iterations ?? 20} elapsed=${elapsedH.toFixed(1)}h`;

    if (state.status === 'blocked') {
      line += `\n  BLOCKED — see .athena/continuous/${entry.name}/BLOCKED.md (do NOT auto-resume per policy).`;
    } else if (state.status === 'running') {
      line += `\n  RUNNING from a prior session — verify no zombie process; if abandoned, mark status=done in state.json.`;
    }
    lines.push(line);
  }

  return lines.length > 0 ? lines.join('\n') : null;
}

async function main() {
  try {
    const input = await readStdin();
    let data = {};
    try { data = JSON.parse(input); } catch {}

    const cwd = data.cwd || data.directory || process.cwd();
    const messages = [];

    // Load last work context
    const contextPath = join(cwd, '.athena', 'last-context.json');
    const ctx = readJson(contextPath);

    if (ctx?.summary && ctx?.timestamp) {
      const age = Date.now() - new Date(ctx.timestamp).getTime();
      const hoursAgo = Math.floor(age / (1000 * 60 * 60));
      const timeLabel = hoursAgo < 1 ? 'recently' :
        hoursAgo < 24 ? `${hoursAgo}h ago` :
        `${Math.floor(hoursAgo / 24)}d ago`;

      messages.push(`<session-restore>

[LAST WORK CONTEXT] (${timeLabel})

${ctx.summary}
${ctx.files?.length ? `\nModified files: ${ctx.files.join(', ')}` : ''}
${ctx.branch ? `Branch: ${ctx.branch}` : ''}

Treat this as prior-session context only. Prioritize the user's newest request.

</session-restore>

---
`);
    }

    // Surface any active continuous-overnight session so a fresh terminal/session
    // can see autonomous work in progress (or stuck/blocked) and act accordingly.
    const overnight = checkContinuousOvernight(cwd);
    if (overnight) {
      messages.push(`<continuous-overnight>
${overnight}
</continuous-overnight>

---
`);
    }

    if (messages.length > 0) {
      console.log(JSON.stringify({
        continue: true,
        hookSpecificOutput: {
          hookEventName: 'SessionStart',
          additionalContext: messages.join('\n')
        }
      }));
    } else {
      console.log(JSON.stringify({ continue: true, suppressOutput: true }));
    }
  } catch {
    console.log(JSON.stringify({ continue: true, suppressOutput: true }));
  }
}

main();
