#!/usr/bin/env node
/**
 * Athena SessionStart hook
 *
 * Loads last work context from .athena/last-context.json
 * and injects it as a session reminder.
 */

import { existsSync, readFileSync, readdirSync, writeFileSync } from 'fs';
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

// Sessions older than this many hours that are still attention=true get
// auto-demoted to attention=false on session-start. Reason: blocked sessions
// retain attention=true so morning surfacing works, but a 3-week-old blocked
// session indefinitely triggers the stop/cancel-precedence routing rule
// (CLAUDE.md). After STALE_HOURS, we treat the session as user-acknowledged
// and quiet it — BLOCKED.md / SUMMARY.md / decisions.md remain on disk as
// evidence; only the JSON flag flips.
const STALE_HOURS = 24 * 7; // 7 days

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
  const demoted = [];
  for (const entry of entries) {
    const stateFile = join(baseDir, entry.name, 'state.json');
    const state = readJson(stateFile);
    if (!state) continue;
    // Surface sessions where attention=true. The contract:
    //   - running session  → attention=true, status=running   → surfaced (RUNNING notice)
    //   - blocked session  → attention=true, status=blocked   → surfaced (BLOCKED notice — must reach user!)
    //   - cancelled        → attention=false, status=cancelled → quiet (cancel skill wrote both)
    //   - done             → attention=false, status=done      → quiet (graceful completion)
    // Blocked sessions intentionally KEEP attention=true so this filter routes them
    // through the BLOCKED branch below — do NOT "fix" the contract by writing
    // attention=false on block; that silently hides overnight failures.
    //
    // Backward-compat: read state.attention with state.active fallback (older state files
    // used the `active` field name; the rename to `attention` is documented in
    // CLAUDE.md / cancel/SKILL.md / continuous-overnight/SKILL.md).
    const attn = state.attention ?? state.active;
    if (attn !== true) continue;

    const id = state.id || entry.name;
    const startedAt = state.started_at ? new Date(state.started_at) : null;
    const elapsedH = startedAt ? (Date.now() - startedAt.getTime()) / 3.6e6 : 0;

    // Stale auto-demotion: sessions older than STALE_HOURS get attention=false
    // written, then skipped (one-shot demotion + brief notice).
    if (startedAt && elapsedH > STALE_HOURS) {
      try {
        const updated = { ...state, attention: false };
        // Drop legacy active field if present so it doesn't shadow the rename.
        if ('active' in updated) delete updated.active;
        writeFileSync(stateFile, JSON.stringify(updated, null, 2));
        demoted.push(`[continuous-overnight] id=${id} status=${state.status} elapsed=${elapsedH.toFixed(1)}h — STALE (>${STALE_HOURS}h), auto-demoted to attention=false. Artifacts preserved at .athena/continuous/${entry.name}/.`);
      } catch {
        // If write fails, fall through and surface as usual — better noisy than silently broken.
      }
      continue;
    }

    let line = `[continuous-overnight] id=${id} status=${state.status} iter=${state.iteration ?? 0}/${state.max_iterations ?? 20} elapsed=${elapsedH.toFixed(1)}h`;

    if (state.status === 'blocked') {
      line += `\n  BLOCKED — see .athena/continuous/${entry.name}/BLOCKED.md (do NOT auto-resume per policy).`;
    } else if (state.status === 'running') {
      line += `\n  RUNNING from a prior session — verify no zombie process; if abandoned, mark status=done in state.json.`;
    }
    lines.push(line);
  }

  const all = [...lines, ...demoted];
  return all.length > 0 ? all.join('\n') : null;
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
