# Deprecated MCP driver scripts

These files were development harnesses that called Playwright MCP via Node.
**Investigations must NOT use them.**

The agent reads `SKILL.md` and calls Playwright MCP tools directly:
`browser_navigate`, `browser_snapshot`, `browser_click`, `browser_take_screenshot`, etc.

| File | Status |
|------|--------|
| `run_osint_mcp.mjs` | Deprecated |
| `run_full_osint.mjs` | Deprecated |
| `test_mcp_discovery.mjs` | Dev test only |
| `node << 'EOF'` MCP loops | **Forbidden** for investigations — agent calls tools step-by-step |

Allowed scripts: `init_workspace.py`, `verify_accounts.py`, `prune_faces.py`, `build_social_graph.py`, `setup_venv.sh`, `resolve_paths.sh`
