---
name: obsidian
description: Read, search, create, and edit notes in the Obsidian vault.
platforms: [linux, macos, windows]
---

# Obsidian Vault

Use this skill for filesystem-first Obsidian vault work: reading notes, listing notes, searching note files, creating notes, appending content, and adding wikilinks.

## Vault path

Use a known or resolved vault path before calling file tools.

The documented vault-path convention is the `OBSIDIAN_VAULT_PATH` environment variable, for example from `~/.hermes/.env`. If it is unset, use `~/Documents/Obsidian Vault`.

File tools do not expand shell variables. Do not pass paths containing `$OBSIDIAN_VAULT_PATH` to `read_file`, `write_file`, `patch`, or `search_files`; resolve the vault path first and pass a concrete absolute path. Vault paths may contain spaces, which is another reason to prefer file tools over shell commands.

If the vault path is unknown, `terminal` is acceptable for resolving `OBSIDIAN_VAULT_PATH` or checking whether the fallback path exists. Once the path is known, switch back to file tools.

## Install and first-time configuration on macOS

When the user asks to install/configure Obsidian, do the full setup and verify it instead of only describing steps:

1. Check existing state: `/Applications/Obsidian.app`, `command -v brew`, `OBSIDIAN_VAULT_PATH`, and the fallback vault path.
2. If Obsidian is missing and Homebrew is available, install with `brew install --cask obsidian`. This also provides the `obsidian` CLI symlink when the cask supports it.
3. Create the fallback vault if no vault is configured: `~/Documents/Obsidian Vault`, plus `.obsidian/` and an `assets/` folder.
4. Seed minimal safe config files only if they do not exist, such as `.obsidian/app.json`, `.obsidian/appearance.json`, and `.obsidian/core-plugins.json`. Avoid overwriting an existing user's vault settings.
5. Add or normalize `OBSIDIAN_VAULT_PATH` in `~/.hermes/.env`. Prefer a quoted value for paths with spaces, e.g. `OBSIDIAN_VAULT_PATH="/Users/fausto/Documents/Obsidian Vault"`. Do not use shell `%q` escaping in `.env` unless you have verified the consumer parses it correctly.
6. Verify: app version from `/Applications/Obsidian.app/Contents/Info.plist`, `command -v obsidian`, vault `.obsidian` exists, at least one note is readable, and the `OBSIDIAN_VAULT_PATH=` line itself shell-parses to the intended directory.

Pitfall: sourcing the entire `~/.hermes/.env` may fail because unrelated credentials or provider variables can contain syntax not accepted by a plain shell. To verify only the Obsidian line, grep the `OBSIDIAN_VAULT_PATH=` line and `eval` just that line, then test the resulting directory.

## Read a note

Use `read_file` with the resolved absolute path to the note. Prefer this over `cat` because it provides line numbers and pagination.

## List notes

Use `search_files` with `target: "files"` and the resolved vault path. Prefer this over `find` or `ls`.

- To list all markdown notes, use `pattern: "*.md"` under the vault path.
- To list a subfolder, search under that subfolder's absolute path.

## Search

Use `search_files` for both filename and content searches. Prefer this over `grep`, `find`, or `ls`.

- For filenames, use `search_files` with `target: "files"` and a filename `pattern`.
- For note contents, use `search_files` with `target: "content"`, the content regex as `pattern`, and `file_glob: "*.md"` when you want to restrict matches to markdown notes.

## Create a note

Use `write_file` with the resolved absolute path and the full markdown content. Prefer this over shell heredocs or `echo` because it avoids shell quoting issues and returns structured results.

## Append to a note

Prefer a native file-tool workflow when it is not awkward:

- Read the target note with `read_file`.
- Use `patch` for an anchored append when there is stable context, such as adding a section after an existing heading or appending before a known trailing block.
- Use `write_file` when rewriting the whole note is clearer than constructing a fragile patch.

For an anchored append with `patch`, replace the anchor with the anchor plus the new content.

For a simple append with no stable context, `terminal` is acceptable if it is the clearest safe option.

## Targeted edits

Use `patch` for focused note changes when the current content gives you stable context. Prefer this over shell text rewriting.

## Wikilinks

Obsidian links notes with `[[Note Name]]` syntax. When creating notes, use these to link related content.
