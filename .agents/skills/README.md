# Engineering skill installation notes

Project instructions: see `/AGENTS.md`. The repository engineering constitution is at `.specify/memory/constitution.md`. Anti-Slop core rules are included in `/antislop.md`.

Upstream sources:
- Matt Pocock engineering skills: https://github.com/mattpocock/skills
- Anti-Slop modular skills: https://github.com/miqdadbadjuber/anti-slop
- GitHub Spec Kit: https://github.com/github/spec-kit
- UI/UX Pro Max: https://github.com/nextlevelbuilder/ui-ux-pro-max-skill

Install selected Matt Pocock skills into the Codex project with `npx skills@latest add mattpocock/skills -a codex`. Choose TDD, diagnosing-bugs, codebase-design, and code-review.

The Anti-Slop core is already vendored. To install its modular skills, use `npx skills@latest add miqdadbadjuber/anti-slop --all -a codex`.

Install Spec Kit with `uv tool install specify-cli`, then verify with `specify version`. This repository already has feature specs under `specs/`; follow the official existing-project adoption guidance before generating templates or migrating artifacts.

This is a Streamlit application. Install the complete UI/UX Pro Max skill and its searchable design data with `npx ui-ux-pro-max-cli init --ai codex`. The CLI is the supported installation path; a partial copied prompt is not the full package.

Review installer diffs before accepting updates. Do not force-overwrite customized agent files or commit machine-specific global settings.