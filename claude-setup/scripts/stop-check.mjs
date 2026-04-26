#!/usr/bin/env node
/**
 * Athena Stop hook
 *
 * 1. Saves last work context to .athena/last-context.json
 * 2. Runs build check if project has a build system
 */

import { execFileSync } from 'child_process';
import { existsSync, mkdirSync, readFileSync, writeFileSync, readdirSync } from 'fs';
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

function tryExec(cmd, args, cwd, timeoutMs = 20000) {
  try {
    const out = execFileSync(cmd, args, {
      encoding: 'utf-8',
      timeout: timeoutMs,
      cwd,
      stdio: ['pipe', 'pipe', 'pipe']
    }).trim();
    return { ok: true, out };
  } catch (e) {
    return { ok: false, out: (e.stderr?.trim() || e.stdout?.trim() || '').slice(0, 500) };
  }
}

function getGitInfo(cwd) {
  try {
    const branch = execFileSync('git', ['branch', '--show-current'], {
      encoding: 'utf-8', cwd, stdio: ['pipe', 'pipe', 'pipe']
    }).trim();
    const diff = execFileSync('git', ['diff', '--name-only'], {
      encoding: 'utf-8', cwd, stdio: ['pipe', 'pipe', 'pipe']
    }).trim();
    const staged = execFileSync('git', ['diff', '--cached', '--name-only'], {
      encoding: 'utf-8', cwd, stdio: ['pipe', 'pipe', 'pipe']
    }).trim();
    const files = [...new Set([...diff.split('\n'), ...staged.split('\n')].filter(Boolean))];
    return { branch, files };
  } catch {
    return { branch: '', files: [] };
  }
}

function saveLastContext(cwd, data) {
  try {
    const dir = join(cwd, '.athena');
    if (!existsSync(dir)) mkdirSync(dir, { recursive: true });
    writeFileSync(join(dir, 'last-context.json'), JSON.stringify(data, null, 2));
  } catch {}
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
    if (!existsSync(stateFile)) continue;

    let state;
    try { state = JSON.parse(readFileSync(stateFile, 'utf-8')); } catch { continue; }
    // Read state.attention with state.active fallback (rename — see session-start.mjs).
    // Surface running OR blocked sessions; quiet only cancelled/done.
    const attn = state.attention ?? state.active;
    if (!attn && state.status !== 'blocked') continue;

    const startedAt = state.started_at ? new Date(state.started_at) : null;
    const elapsedH = startedAt ? (Date.now() - startedAt.getTime()) / 3.6e6 : 0;
    const maxH = state.max_hours ?? 8;
    const iter = state.iteration ?? 0;
    const maxIter = state.max_iterations ?? 20;

    let line = `[continuous-overnight] id=${state.id} status=${state.status} iter=${iter}/${maxIter} elapsed=${elapsedH.toFixed(1)}h/${maxH}h`;

    if (state.status === 'blocked') {
      const blockedFile = join(baseDir, entry.name, 'BLOCKED.md');
      if (existsSync(blockedFile)) {
        line += `\n  BLOCKED — see .athena/continuous/${entry.name}/BLOCKED.md (do NOT auto-resume per policy).`;
      }
    } else if (state.status === 'running') {
      if (elapsedH >= maxH) {
        line += `\n  WALL-TIME CAP HIT — finalize as graceful done (status=done) and write SUMMARY.md.`;
      } else if (elapsedH > maxH * 0.9) {
        line += `\n  WARNING — ${(maxH - elapsedH).toFixed(1)}h until wall-time cap.`;
      }
      if (iter >= maxIter) {
        line += `\n  ITERATION CAP HIT — finalize as graceful done.`;
      }
    }

    lines.push(line);
  }

  return lines.length > 0 ? lines.join('\n') : null;
}

function detectBuildCheck(cwd) {
  if (existsSync(join(cwd, 'pyproject.toml')) || existsSync(join(cwd, 'setup.py'))) {
    return { type: 'python', cmd: 'python', args: ['-m', 'py_compile'] };
  }
  if (existsSync(join(cwd, 'go.mod'))) {
    return { type: 'go', cmd: 'go', args: ['build', './...'] };
  }
  if (existsSync(join(cwd, 'package.json'))) {
    try {
      const pkg = JSON.parse(readFileSync(join(cwd, 'package.json'), 'utf-8'));
      if (pkg.scripts?.build) return { type: 'node', cmd: 'npm', args: ['run', 'build'] };
      if (pkg.scripts?.typecheck) return { type: 'node', cmd: 'npm', args: ['run', 'typecheck'] };
    } catch {}
  }
  return null;
}

async function main() {
  try {
    const input = await readStdin();
    let data = {};
    try { data = JSON.parse(input); } catch {}

    const cwd = data.cwd || process.cwd();
    const stopReason = data.stop_reason || 'end_turn';
    const messages = [];

    // 1. Save last work context
    const git = getGitInfo(cwd);
    if (git.files.length > 0 || git.branch) {
      const summary = git.files.length > 0
        ? `Working on ${git.files.length} file(s): ${git.files.slice(0, 5).join(', ')}${git.files.length > 5 ? ` (+${git.files.length - 5} more)` : ''}`
        : `On branch ${git.branch}, no uncommitted changes.`;

      saveLastContext(cwd, {
        summary,
        files: git.files.slice(0, 20),
        branch: git.branch,
        timestamp: new Date().toISOString()
      });
    }

    // 2. Continuous-overnight autonomy awareness
    const overnight = checkContinuousOvernight(cwd);
    const overnightActive = overnight !== null;
    if (overnight) {
      messages.push(`<continuous-overnight>\n${overnight}\n</continuous-overnight>`);
    }

    // 3. Build check (only on normal stop with uncommitted changes; skip in autonomous mode to avoid prompting noise)
    if (stopReason === 'end_turn' && !overnightActive) {
      const build = detectBuildCheck(cwd);
      if (build && git.files.length > 0) {
        const result = tryExec(build.cmd, build.args, cwd);
        if (!result.ok) {
          messages.push(`<build-check>
[BUILD FAILED] (${build.type}: ${build.cmd} ${build.args.join(' ')})

${result.out}

Fix the build errors before concluding.
</build-check>`);
        }
      }
    }

    if (messages.length > 0) {
      console.log(JSON.stringify({
        continue: true,
        hookSpecificOutput: {
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
