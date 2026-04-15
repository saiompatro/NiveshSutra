# Prompt Optimization & Context Engineering Research

## Sources
1. Anthropic Claude Code docs (code.claude.com/docs)
2. HumanLayer Blog - Writing a Good CLAUDE.md
3. UX Planet - CLAUDE.md Best Practices
4. Medium - Complete Guide to AI Agent Memory Files
5. ClaudeFast Code Kit - Token Usage Optimization
6. Caveman mode - Token reduction via terse output
7. Stack Builders - Beyond AGENTS.md

## Key Takeaways (Applied in This Build)

### CLAUDE.md & Context Files
1. Keep CLAUDE.md under 300 lines with WHY/WHAT/HOW structure
2. Use progressive disclosure — split task-specific instructions into separate .md files
3. Include exact command strings for common operations (verbatim copy)
4. Add compaction rules to preserve critical context during summarization

### Token Efficiency
5. Load domain knowledge on-demand, not all upfront (~15K tokens saved per session)
6. State critical constraints at prompt start, not buried at end
7. Use terse output style — cuts 65% of tokens with no quality loss
8. Keep prompt caching enabled (5-minute TTL window)
9. Parallelize with subagents for focused context windows

### Repository Documentation
10. Create supporting docs: ARCHITECTURE.md, CONTRIBUTING.md — not one monolithic file
11. Add examples folder with code patterns > writing rules
12. Context engineering (selection, compression, ordering) > prompt wording

### Execution Patterns
13. Use deterministic workflows over freestyle prompting
14. Enforce repeatable execution and role-based agent specialization
15. Batch related edits before reporting progress

## Rules Applied in NiveshSutra Build
1. CLAUDE.md with exact dev commands and project conventions
2. Separate docs/ folder for architecture, research, API documentation
3. Subagent parallelization for independent tasks (ML pipelines, frontend)
4. Terse status updates (<8 lines) in chat
5. Files for research notes instead of chat-based explanations
6. Progressive context: CLAUDE.md → docs/architecture.md → inline comments
7. Batch-write files then commit, rather than file-by-file reporting
