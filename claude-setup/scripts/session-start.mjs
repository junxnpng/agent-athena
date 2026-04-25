#!/usr/bin/env node
/**
 * Athena SessionStart hook
 *
 * Loads last work context from .athena/last-context.json
 * and injects it as a session reminder.
 */

import { existsSync, readFileSync } from 'fs';
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
