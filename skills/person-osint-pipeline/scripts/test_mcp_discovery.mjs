#!/usr/bin/env node
/**
 * Playwright MCP integration test for person-osint-pipeline.
 * Validates MCP tools work — does NOT replace the agent workflow in SKILL.md.
 */
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";
import fs from "node:fs/promises";

const MCP_URL = process.env.PLAYWRIGHT_MCP_URL || "http://localhost:8931/mcp";

async function callTool(client, name, args = {}) {
  const result = await client.callTool({ name, arguments: args });
  const text = result.content
    ?.map((c) => (c.type === "text" ? c.text : JSON.stringify(c)))
    .join("\n");
  return { result, text: text || "" };
}

async function main() {
  const transport = new StreamableHTTPClientTransport(new URL(MCP_URL));
  const client = new Client({ name: "osint-skill-test", version: "1.0.0" });
  await client.connect(transport);

  const tools = await client.listTools();
  console.log("MCP connected. Tool count:", tools.tools.length);

  const workspace = process.env.WORKSPACE;
  const refPath = process.env.REFERENCE_PHOTO;
  const handleDir = "samreedh-bhuyan_linkedin";
  const profileUrl = "https://www.linkedin.com/in/samreedh-bhuyan";

  // 1) Capture GitHub avatar as reference (direct image URL — not full page)
  if (refPath) {
    console.log("\n=== GitHub avatar (reference photo) ===");
    await callTool(client, "browser_navigate", {
      url: "https://avatars.githubusercontent.com/u/59220054?v=4",
    });
    const avatarShot = await callTool(client, "browser_take_screenshot", {
      filename: refPath,
      type: "jpeg",
    });
    console.log(avatarShot.text.slice(0, 300));
  }

  // 2) Google name search
  const query = encodeURIComponent("site:linkedin.com/in Samreedh Bhuyan");
  console.log("\n=== Google LinkedIn search ===");
  await callTool(client, "browser_navigate", {
    url: `https://www.google.com/search?q=${query}`,
  });
  const snap = await callTool(client, "browser_snapshot", {});
  const linkedinMatch = snap.text.match(
    /linkedin\.com\/in\/[a-zA-Z0-9_-]+/i
  );
  const discovered = linkedinMatch
    ? `https://www.${linkedinMatch[0]}`
    : profileUrl;
  console.log("Discovered:", discovered);

  // 3) LinkedIn profile screenshot
  if (workspace) {
    const accountDir = `${workspace}/accounts/${handleDir}`;
    await fs.mkdir(accountDir, { recursive: true });
    const screenshotPath = `${accountDir}/profile.png`;

    console.log("\n=== LinkedIn profile screenshot ===");
    await callTool(client, "browser_navigate", { url: discovered });
    const shot = await callTool(client, "browser_take_screenshot", {
      filename: screenshotPath,
      type: "png",
      fullPage: false,
    });
    console.log(shot.text.slice(0, 400));
    console.log("Saved:", screenshotPath);

    // Update accounts_index.md with candidate row
    const indexPath = `${workspace}/accounts_index.md`;
    let index = await fs.readFile(indexPath, "utf8");
    if (!index.includes(discovered)) {
      index = index.replace(
        "| instagram | https://instagram.com/example | example_ig | CANDIDATE | — |",
        `| linkedin | ${discovered} | ${handleDir} | HARVESTED | ${discovered} |`
      );
      await fs.writeFile(indexPath, index);
      console.log("Updated accounts_index.md with LinkedIn candidate");
    }
  }

  await client.close();
  console.log("\nPlaywright MCP test complete.");
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
