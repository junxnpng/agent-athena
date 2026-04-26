#!/usr/bin/env node
/**
 * Athena agent-skill consistency check.
 *
 * Catches three regression classes:
 *   (a) `athena:<name>` references inside SKILL.md to agents/skills that no
 *       longer exist (rename/remove without updating callers).
 *   (b) `skills/<dir>/SKILL.md` frontmatter `name:` field drifting from `<dir>`
 *       (would break invocation since Claude Code uses dir name as the skill id).
 *   (c) CLAUDE.md mentions of skills (`/athena:<name>` or bare `<name>` in the
 *       <skills> catalog block) that no longer resolve to a `skills/<name>/SKILL.md`.
 *
 * Static grep is cheap and runs both as a hook step and via setup.sh / CLI.
 */

import { readdirSync, readFileSync, existsSync } from 'fs';
import { join, basename } from 'path';

function frontmatterName(skillFile) {
  try {
    const content = readFileSync(skillFile, 'utf-8');
    const match = content.match(/^---\s*\r?\n([\s\S]*?)\r?\n---/);
    if (!match) return null;
    const nameLine = match[1].split('\n').find((l) => /^\s*name\s*:/.test(l));
    if (!nameLine) return null;
    return nameLine.replace(/^\s*name\s*:\s*/, '').trim();
  } catch {
    return null;
  }
}

export function checkAgentSkillConsistency(pluginRoot) {
  const agentsDir = join(pluginRoot, 'agents');
  const skillsDir = join(pluginRoot, 'skills');
  const claudeMdPath = join(pluginRoot, 'CLAUDE.md');
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

  // (a) athena: refs inside skill files
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

    // (b) frontmatter name must equal dir name
    const fmName = frontmatterName(skillFile);
    if (fmName !== null && fmName !== skillName) {
      issues.push({
        location: `skills/${skillName}/SKILL.md`,
        referenced: `frontmatter name: "${fmName}"`,
        fix: `frontmatter name must equal directory name. Set name: ${skillName} or rename the directory to ${fmName}.`,
      });
    }
  }

  // (c) CLAUDE.md skill mentions must resolve to skills/<name>/SKILL.md
  if (existsSync(claudeMdPath)) {
    const claudeContent = readFileSync(claudeMdPath, 'utf-8');

    // /athena:<name> mentions anywhere
    const slashRefs = [...claudeContent.matchAll(/\/athena:([a-z][a-z0-9-]*)/g)];
    const seenSlash = new Set();
    for (const m of slashRefs) {
      const refName = m[1];
      if (seenSlash.has(refName)) continue;
      seenSlash.add(refName);
      if (!skills.has(refName) && !agents.has(refName)) {
        issues.push({
          location: 'CLAUDE.md',
          referenced: `/athena:${refName}`,
          fix: `Either add skills/${refName}/ (or agents/${refName}.md), or remove the CLAUDE.md mention.`,
        });
      }
    }

    // Bare skill names listed in the <skills> catalog block.
    // We narrowly scope to lines of form `- <name> —` (the catalog format used in CLAUDE.md).
    const skillsBlockMatch = claudeContent.match(/<skills>([\s\S]*?)<\/skills>/);
    if (skillsBlockMatch) {
      const block = skillsBlockMatch[1];
      const bareMentions = [...block.matchAll(/^\s*-\s+([a-z][a-z0-9-]*)\s+—/gm)];
      const seenBare = new Set();
      for (const m of bareMentions) {
        const refName = m[1];
        if (seenBare.has(refName)) continue;
        seenBare.add(refName);
        if (!skills.has(refName)) {
          issues.push({
            location: 'CLAUDE.md (<skills> block)',
            referenced: refName,
            fix: `CLAUDE.md catalog mentions skill "${refName}" but no skills/${refName}/SKILL.md exists. Add the skill or remove the catalog line.`,
          });
        }
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
    console.log(`OK — ${scanned} skill(s) scanned, all athena: refs resolve, frontmatter name matches dir, CLAUDE.md catalog clean.`);
    process.exit(0);
  } else {
    console.error(`FAIL — ${issues.length} issue(s):`);
    for (const i of issues) {
      console.error(`  ${i.location}: ${i.referenced} unresolved`);
      console.error(`    fix: ${i.fix}`);
    }
    process.exit(1);
  }
}
