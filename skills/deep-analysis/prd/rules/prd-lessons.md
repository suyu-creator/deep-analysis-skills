# PRD Lessons

Never write to `.claude/prd-lessons.md` without explicit user approval.

The prd-reviewer PROPOSES lessons in the review document. The create-prd orchestrator presents proposals to the user. The user decides which to accept. Only after the user explicitly approves specific lessons (by name or number) may any agent append them to the file.

If the user says "skip", "none", or does not approve — write nothing.

This rule applies to all agents, skills, and conversations in this project.
