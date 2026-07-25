# Claude Code and Codex host adapter

This plugin supports both Claude Code and Codex. Apply this adapter before following any host-specific orchestration wording in the calling `SKILL.md`; this file overrides conflicting details about agent APIs, model names, and concurrency, but never changes the review criteria or read-only boundaries.

## Dispatch

- **Claude Code:** prefer the bundled typed agents named in the skill. If they are unavailable, use a general-purpose sub-agent and inline the corresponding brief from `<plugin-root>/agents/`.
- **Codex:** bundled files under `agents/` are briefs, not registered sub-agent types. Read the relevant brief, then use Codex's available sub-agent/collaboration mechanism to spawn a general sub-agent with that brief plus the scoped evidence. Give each task a stable lens/cartographer name. Do not claim a typed `review-strict:*` agent exists.
- Respect the host's actual concurrency limit. Start as many independent lenses as fit, then dispatch the remaining lenses as slots become available. "In parallel" means maximum safe concurrency, not that every lens must start in one call.
- If the current host has no sub-agent capability, run the documented `--fast` path inline and state that the fan-out was unavailable.

## Models

- `sonnet`, `opus`, and `haiku` are Claude model selectors. Use them only on a host that advertises those selectors.
- On Codex, inherit the session model by default. Pass a model override only when the requested value is explicitly supported by the current Codex host. Never translate a Claude selector into a guessed Codex model.
- An unsupported `--model` value is not fatal: explain that it is unavailable on this host and inherit the session model. The skeptic/verification pass always inherits the session model.

## Tools and paths

- Translate conceptual tool names to the host's available equivalents: `Read/Grep/Glob` means read-only filesystem/search operations; `Bash` means the host shell tool; `Write/Edit` means the host patch or edit tool.
- Resolve `<plugin-root>` from the installed skill location. All bundled briefs and references stay inside the plugin root.
- Preserve every mutation boundary in the calling skill. Lens, cartographer, and skeptic agents are read-only even when the host offers write tools.
