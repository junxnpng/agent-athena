#!/usr/bin/env node
/**
 * Athena agent-skill consistency check.
 *
 * Catches the regression class where an agent is removed/renamed but a SKILL.md
 * still references it via `athena:<name>` — would fail at runtime when the
 * skill is invoked. Static grep is cheap and runs both as a hook step and via
 * setup.sh / CLI.
 */

import { readdirSync, readFileSync, existsSync } from 'fs';
import { join, basename } from 'path';

export function checkAgentSkillConsistency(pluginRoot) {
  const agentsDir = join(pluginRoot, 'agents');
  const skillsDir = join(pluginRoot, 'skills');
  if (!existsSync(agentsDir) || !existsSync(skillsDir)) {
    return { issues: [], scanned: 0 };
  }

  const agents = new Set(
    readdirSync(agentsDir)
      .filter((f) => f.endsWith('.md'))
      .map((f) => basename(f, '.md'))
  );

  const skills = new Set(
    readdirSync(skillsDir, { withFileTypes: true })
      .filter((d) => d.isDirectory())
      .map((d) => d.name)
  );

  const valid = new Set([...agents, ...skills]);
  const issues = [];
  let scanned = 0;

  for (const skillName of skills) {
    const skillFile = join(skillsDir, skillName, 'SKILL.md');
    if (!existsSync(skillFile)) continue;
    scanned++;

    const content = readFileSync(skillFile, 'utf-8');
    const refs = [...content.matchAll(/athena:([a-z][a-z0-9-]*)/g)];
    const seenInSkill = new Set();

    for (const m of refs) {
      const refName = m[1];
      if (seenInSkill.has(refName)) continue;
      seenInSkill.add(refName);
      if (!valid.has(refName)) {
        issues.push({
          location: `skills/${skillName}/SKILL.md`,
          referenced: `athena:${refName}`,
          fix: `Either add agents/${refName}.md, add skills/${refName}/, or remove the reference.`,
        });
      }
    }
  }

  return { issues, scanned };
}

// CLI mode: `node check-consistency.mjs <pluginRoot>`
const isMain = import.meta.url === `file://${process.argv[1]}`;
if (isMain) {
  const root = process.argv[2];
  if (!root) {
    console.error('Usage: check-consistency.mjs <pluginRoot>');
    process.exit(2);
  }
  const { issues, scanned } = checkAgentSkillConsistency(root);
  if (issues.length === 0) {
    console.log(`OK — ${scanned} skill(s) scanned, all athena: references resolve.`);
    process.exit(0);
  } else {
    console.error(`FAIL — ${issues.length} broken reference(s):`);
    for (const i of issues) {
      console.error(`  ${i.location}: ${i.referenced} unresolved`);
      console.error(`    fix: ${i.fix}`);
    }
    process.exit(1);
  }
}
