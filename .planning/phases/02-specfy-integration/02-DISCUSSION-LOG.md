# Phase 2: Specfy Integration - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md -- this log preserves the alternatives considered.

**Date:** 2026-04-08
**Phase:** 02-specfy-integration
**Areas discussed:** Error messaging, Timeout & failure, Runner return contract, First-run experience

---

## Error Messaging

### Error Style

| Option | Description | Selected |
|--------|-------------|----------|
| Rich panels | Rich-formatted error panels with color, clear title, and actionable instructions | ✓ |
| Plain stderr | Simple text to stderr, minimal, no formatting | |
| You decide | Let Claude pick | |

**User's choice:** Rich panels
**Notes:** Consistent with the tool's Rich-based output

### Verbosity

| Option | Description | Selected |
|--------|-------------|----------|
| Actionable minimum | What went wrong + one clear next step. No stack traces unless --verbose | ✓ |
| Detailed diagnostics | Include system info, paths checked, versions found | |
| You decide | Let Claude pick | |

**User's choice:** Actionable minimum
**Notes:** None

---

## Timeout & Failure

### Timeout Behavior

| Option | Description | Selected |
|--------|-------------|----------|
| Abort with clear error | Kill process, show Rich error, suggest smaller path. No retry. | ✓ |
| Retry once, then abort | Auto retry one time, then abort | |
| You decide | Let Claude pick | |

**User's choice:** Abort with clear error
**Notes:** None

### Bad Output Handling

| Option | Description | Selected |
|--------|-------------|----------|
| Fail with error | Non-zero exit or bad JSON = hard failure. Show stderr in Rich panel. | ✓ |
| Partial results if possible | Try to extract whatever output exists | |
| You decide | Let Claude pick | |

**User's choice:** Fail with error
**Notes:** None

---

## Runner Return Contract

### Return Type

| Option | Description | Selected |
|--------|-------------|----------|
| Exceptions for errors | Return raw dict on success. Raise typed exceptions on failure. | ✓ |
| Result object | Return result dataclass with success/failure flag | |
| You decide | Let Claude pick | |

**User's choice:** Exceptions for errors (NodeNotFoundError, SpecfyTimeoutError, SpecfyError)
**Notes:** CLI layer catches and displays Rich panels

---

## First-Run Experience

### First-Run Download

| Option | Description | Selected |
|--------|-------------|----------|
| Tell the user | Print brief message before npx call: "Downloading stack analyser (first run only)..." | ✓ |
| Rich spinner/progress | Show Rich spinner while npx downloads | |
| Silent -- just wait | Don't say anything, let npx handle it | |
| You decide | Let Claude pick | |

**User's choice:** Tell the user
**Notes:** Simple message, no spinner

---

## Claude's Discretion

- Exact exception class hierarchy and base class design
- Internal module structure within src/naz/detection/
- How to detect first-run vs subsequent runs
- Test fixture structure for mocked Specfy output

## Deferred Ideas

None -- discussion stayed within phase scope
