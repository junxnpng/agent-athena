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
Read .athena/state/research.json — if active, cancel research
```

### 2. Cancel each active mode
- Remove the state file
- Report: "[mode] cancelled. State cleaned up."

### 3. Force mode (--force)
- Delete entire `.athena/state/` directory contents
- Report: "All athena state cleared."

## Messages

| Mode | Message |
|------|---------|
| Autopilot | "Autopilot cancelled at phase: {phase}." |
| Ralph | "Ralph cancelled. {N}/{total} criteria completed." |
| Research | "Research cancelled." |
| Force | "All athena state cleared." |
| None | "No active modes detected." |
