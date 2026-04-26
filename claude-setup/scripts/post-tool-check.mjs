#!/usr/bin/env node
/**
 * Athena PostToolUse hook
 *
 * Runs lint and typecheck on files modified by Edit/Write tools.
 * - Python: ruff (lint), mypy/pyright (typecheck)
 * - Go: golangci-lint (lint), go vet (typecheck)
 */

import { execFileSync } from 'child_process';
import { existsSync } from 'fs';
import { extname, dirname, join } from 'path';
import { checkAgentSkillConsistency } from './check-consistency.mjs';

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

function tryExec(cmd, args, timeoutMs = 10000) {
  try {
    return execFileSync(cmd, args, {
      encoding: 'utf-8',
      timeout: timeoutMs,
      stdio: ['pipe', 'pipe', 'pipe']
    }).trim();
  } catch (e) {
    return (e.stdout?.trim() || e.stderr?.trim() || '').slice(0, 500);
  }
}

function cmdExists(cmd) {
  try {
    execFileSync('which', [cmd], { stdio: 'pipe' });
    return true;
  } catch {
    return false;
  }
}

function findPluginRoot(filePath) {
  let dir = dirname(filePath);
  for (let i = 0; i < 10; i++) {
    if (existsSync(join(dir, '.claude-plugin', 'plugin.json'))) {
      return dir;
    }
    const parent = dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  return null;
}

async function main() {
  try {
    const input = await readStdin();
    let data = {};
    try { data = JSON.parse(input); } catch {}

    const toolName = data.tool_name || '';
    if (!['Edit', 'Write'].includes(toolName)) {
      console.log(JSON.stringify({ continue: true, suppressOutput: true }));
      return;
    }

    const filePath = data.tool_input?.file_path || '';
    if (!filePath || !existsSync(filePath)) {
      console.log(JSON.stringify({ continue: true, suppressOutput: true }));
      return;
    }

    const ext = extname(filePath);
    const results = [];

    // Python files
    if (ext === '.py') {
      if (cmdExists('ruff')) {
        const lint = tryExec('ruff', ['check', '--no-fix', filePath]);
        if (lint) results.push(`[ruff] ${lint}`);
      }
      if (cmdExists('mypy')) {
        const tc = tryExec('mypy', ['--no-error-summary', filePath]);
        if (tc && !tc.includes('Success')) results.push(`[mypy] ${tc}`);
      } else if (cmdExists('pyright')) {
        const tc = tryExec('pyright', [filePath]);
        if (tc && !tc.includes('0 errors')) results.push(`[pyright] ${tc}`);
      }
    }

    // Athena plugin invariant: agent/skill consistency
    // Triggers when an agent .md / SKILL.md / CLAUDE.md inside a Claude Code plugin is edited.
    // CLAUDE.md is included because it documents the skill catalog and routes — drift between
    // CLAUDE.md mentions and skills/ dirs is exactly what the consistency checker now scans for.
    if (ext === '.md') {
      const pluginRoot = findPluginRoot(filePath);
      if (
        pluginRoot &&
        (filePath.includes(`${pluginRoot}/agents/`) ||
          filePath.includes(`${pluginRoot}/skills/`) ||
          filePath === `${pluginRoot}/CLAUDE.md`)
      ) {
        const { issues } = checkAgentSkillConsistency(pluginRoot);
        if (issues.length > 0) {
          const lines = issues.map((i) => `  ${i.location}: ${i.referenced} unresolved\n    fix: ${i.fix}`);
          results.push(`[agent-skill consistency] ${issues.length} broken reference(s):\n${lines.join('\n')}`);
        }
      }
    }

    // Go files
    if (ext === '.go') {
      if (cmdExists('golangci-lint')) {
        const lint = tryExec('golangci-lint', ['run', filePath]);
        if (lint) results.push(`[golangci-lint] ${lint}`);
      }
      const vet = tryExec('go', ['vet', filePath]);
      if (vet) results.push(`[go vet] ${vet}`);
    }

    if (results.length > 0) {
      console.log(JSON.stringify({
        continue: true,
        hookSpecificOutput: {
          additionalContext: `<post-tool-check>\n${results.join('\n\n')}\n</post-tool-check>`
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
