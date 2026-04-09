---
name: json-prettify
description: "Clean up and pretty-print messy JSON strings. Use this skill whenever a user pastes a JSON string that looks broken, escaped, double-escaped, wrapped in extra quotes, or mixed with log/console garbage — and wants to see clean formatted JSON. Trigger on phrases like: 'fix this JSON', 'prettify JSON', 'format this JSON', 'clean up JSON', 'unescape JSON', 'parse this string as JSON', or when the user simply pastes a mangled JSON blob and asks to make it readable."
---

# JSON Prettify

Turn messy, escaped, or garbled JSON strings into clean, human-readable JSON output.

## Why this skill exists

JSON strings often arrive in a broken or unreadable state — copied from logs, API responses, debug consoles, or stringified storage. Manually cleaning up escaping and formatting is tedious and error-prone. This skill automates the cleanup so the user instantly gets valid, nicely formatted JSON.

## How to process the input

Work through these cleanup steps in order. Each step handles a progressively messier input. Stop as soon as you get valid JSON.

### Step 1: Try parsing as-is
The input might already be valid JSON, just not formatted. Try parsing it directly.

### Step 2: Strip outer quotes
If the entire string is wrapped in quotes (single or double), remove them and try again.

### Step 3: Unescape backslash sequences
Replace `\"` with `"`, `\\` with `\`, `\n` with newlines, `\t` with tabs.

### Step 4: Handle double (or triple) escaping
Repeat the unescape step until no more `\"` sequences remain.

### Step 5: Extract JSON from surrounding text
Find the first `{` or `[` and its matching closing bracket. Extract just that part and retry from Step 1.

### Step 6: Fix common syntax issues
Trailing commas, single quotes, unquoted keys, missing quotes around string values.

## Output format

Output the result as a fenced JSON code block with 2-space indentation. If the input cannot be parsed, tell the user what went wrong.
