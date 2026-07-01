#!/usr/bin/env node
/** Single MCP tool call — agent decides each invocation. Not for loops. */
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";

const [tool, jsonArgs] = process.argv.slice(2);
if (!tool) {
  console.error("Usage: mcp_one.mjs <tool> '<json-args>'");
  process.exit(1);
}
const args = jsonArgs ? JSON.parse(jsonArgs) : {};
const c = new Client({ name: "agent-step", version: "1.0.0" });
await c.connect(new StreamableHTTPClientTransport(new URL("http://localhost:8931/mcp")));
const r = await c.callTool({ name: tool, arguments: args });
const text = r.content?.map((x) => (x.type === "text" ? x.text : JSON.stringify(x))).join("\n");
console.log(text || "(empty)");
await c.close();
