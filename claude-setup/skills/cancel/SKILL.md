---
name: cancel
description: Cancel active athena mode and clean up state
argument-hint: "[--force]"
---

# Cancel Skill

Stop the active athena mode and clean up state files.

## Usage

```
/athena:cancel           # Smart cancel — detect and cancel active mode
/athena:cancel --force   # Force clear all state files
```

Or say: "cancel", "stop", "abort"

## What It Does

1. **Detect active mode**: Read `.athena/state/` for active state files
2. **Cancel in order**: autopilot → ralph → other modes
3. **Clean up**: Remove state files, report what was cancelled

## Implementation

When invoked:

### 1. Check for active modes
```
Read .athena/state/autopilot.json — if active, cancel autopilot
Read .athena/state/ralph.json — if active, cancel ralph
List .athena/continuous/*/state.json — for any with status=running, mark status=blocked + write BLOCKED.md (cancellation)
```

### 2. Cancel each active mode
- For autopilot/ralph: remove the state file
- For continuous-overnight: never delete `.athena/continuous/<id>/` (preserves decisions.md + results/ for review). Mark status=blocked, write BLOCKED.md with reason="user-cancelled".
- Report: "[mode] cancelled. State cleaned up."

### 3. Force mode (--force)
- Delete `.athena/state/` directory contents (autopilot/ralph)
- Do NOT touch `.athena/continuous/` — preserve overnight artifacts even on force cancel
- Report: "All athena state cleared (continuous-overnight artifacts preserved)."

## Messages

| Mode | Message |
|------|---------|
| Autopilot | "Autopilot cancelled at phase: {phase}." |
| Ralph | "Ralph cancelled. {N}/{total} criteria completed." |
| Continuous-overnight | "Continuous-overnight {id} blocked at iteration {N}. Artifacts preserved at .athena/continuous/{id}/." |
| Force | "All athena state cleared (continuous-overnight artifacts preserved)." |
| None | "No active modes detected." |
