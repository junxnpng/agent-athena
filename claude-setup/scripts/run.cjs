#!/usr/bin/env node
'use strict';
/**
 * Athena hook runner (run.cjs)
 *
 * Spawns target .mjs hook scripts using the current Node binary.
 * Reads timeout from hooks.json so hooks never block Claude Code.
 */

const { spawnSync } = require('child_process');
const { existsSync, readFileSync } = require('fs');
const { join, basename, dirname } = require('path');

const target = process.argv[2];
if (!target || !existsSync(target)) {
  process.exit(0);
}

// Resolve hook timeout from hooks.json
function resolveTimeoutMs(targetPath) {
  const pluginRoot = dirname(dirname(targetPath));
  const hooksPath = join(pluginRoot, 'hooks', 'hooks.json');
  if (!existsSync(hooksPath)) return null;

  try {
    const data = JSON.parse(readFileSync(hooksPath, 'utf-8'));
    const scriptName = basename(targetPath);
    const pattern = new RegExp(scriptName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));

    for (const groups of Object.values(data.hooks || {})) {
      for (const group of groups) {
        for (const hook of (group.hooks || [])) {
          if (typeof hook.command === 'string' && pattern.test(hook.command)) {
            const t = Number(hook.timeout);
            if (t > 0) return Math.floor(t * 1000);
          }
        }
      }
    }
  } catch {}
  return null;
}

const timeoutMs = resolveTimeoutMs(target);

const result = spawnSync(
  process.execPath,
  [target, ...process.argv.slice(3)],
  {
    stdio: 'inherit',
    env: process.env,
    ...(timeoutMs ? { timeout: timeoutMs, killSignal: 'SIGKILL' } : {}),
  }
);

if (result.error?.code === 'ETIMEDOUT') {
  process.stderr.write(`[athena] Hook ${basename(target)} timed out after ${timeoutMs}ms\n`);
}

process.exit(result.status ?? 0);
