#!/usr/bin/env node
/**
 * Full Phase 1-2 OSINT run via Playwright MCP (no standalone Playwright CLI).
 */
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";
import fs from "node:fs/promises";
import path from "node:path";

const MCP_URL = process.env.PLAYWRIGHT_MCP_URL || "http://localhost:8931/mcp";
const WORKSPACE = process.env.WORKSPACE;
const REFERENCE = process.env.REFERENCE_PHOTO;
const SUBJECT = process.env.SUBJECT_NAME || "Samreedh Bhuyan";

async function callTool(client, name, args = {}) {
  const result = await client.callTool({ name, arguments: args });
  const text = result.content
    ?.map((c) => (c.type === "text" ? c.text : JSON.stringify(c)))
    .join("\n");
  return text || "";
}

function extractUrls(text, patterns) {
  const found = new Set();
  for (const re of patterns) {
    for (const m of text.matchAll(re)) {
      found.add(m[0].startsWith("http") ? m[0] : `https://${m[0]}`);
    }
  }
  return [...found];
}

function handleFromUrl(url, platform) {
  const u = new URL(url);
  const segs = u.pathname.split("/").filter(Boolean);
  let handle = segs[segs.length - 1] || "unknown";
  if (platform === "linkedin" && segs[0] === "in") handle = segs[1] || handle;
  const suffix = { instagram: "ig", linkedin: "linkedin", x: "x", facebook: "fb" }[platform];
  return suffix && !handle.endsWith(`_${suffix}`) ? `${handle}_${suffix}` : handle;
}

async function googleSearch(client, query) {
  await callTool(client, "browser_navigate", {
    url: `https://www.google.com/search?q=${encodeURIComponent(query)}`,
  });
  return callTool(client, "browser_snapshot", {});
}

async function main() {
  if (!WORKSPACE || !REFERENCE) {
    throw new Error("Set WORKSPACE and REFERENCE_PHOTO env vars");
  }

  const transport = new StreamableHTTPClientTransport(new URL(MCP_URL));
  const client = new Client({ name: "person-osint-run", version: "1.0.0" });
  await client.connect(transport);

  const candidates = [];
  const searches = [
    { platform: "linkedin", query: `site:linkedin.com/in "${SUBJECT}"` },
    { platform: "x", query: `site:x.com "${SUBJECT}"` },
    { platform: "instagram", query: `site:instagram.com "${SUBJECT}"` },
    { platform: "facebook", query: `site:facebook.com "${SUBJECT}"` },
    { platform: "web", query: `"${SUBJECT}" KIIT Bhubaneswar` },
  ];

  console.log("=== Phase 1b: name search ===");
  for (const { platform, query } of searches) {
    const snap = await googleSearch(client, query);
    const patterns =
      platform === "linkedin"
        ? [/linkedin\.com\/in\/[a-zA-Z0-9_-]+/gi]
        : platform === "x"
          ? [/(?:x|twitter)\.com\/[a-zA-Z0-9_]+/gi]
          : platform === "instagram"
            ? [/instagram\.com\/[a-zA-Z0-9_.]+/gi]
            : platform === "facebook"
              ? [/facebook\.com\/[a-zA-Z0-9.]+/gi]
              : [/github\.com\/[a-zA-Z0-9_-]+/gi, /linkedin\.com\/in\/[a-zA-Z0-9_-]+/gi];

    for (const url of extractUrls(snap, patterns)) {
      if (url.includes("/share") || url.includes("/intent")) continue;
      const plat =
        url.includes("linkedin") ? "linkedin"
        : url.includes("instagram") ? "instagram"
        : url.includes("x.com") || url.includes("twitter") ? "x"
        : url.includes("facebook") ? "facebook"
        : url.includes("github") ? "github"
        : platform;
      candidates.push({
        platform: plat,
        profile_url: url.split("?")[0],
        handle_dir: handleFromUrl(url.split("?")[0], plat),
      });
    }
    console.log(`${platform}: ${candidates.length} total candidates so far`);
  }

  // Dedupe
  const seen = new Set();
  const unique = candidates.filter((c) => {
    const k = c.profile_url;
    if (seen.has(k)) return false;
    seen.add(k);
    return true;
  });

  // Always include known GitHub
  unique.push({
    platform: "github",
    profile_url: "https://github.com/markknoffler",
    handle_dir: "markknoffler_github",
  });

  console.log("\n=== Phase 1a: reverse image (Google) ===");
  await callTool(client, "browser_navigate", { url: "https://www.google.com/imghp" });
  const imgHome = await callTool(client, "browser_snapshot", {});
  if (/Search by image|camera|upload/i.test(imgHome)) {
    console.log("Google Images loaded (reverse search available via browser_file_upload)");
  }

  console.log("\n=== Phase 2: profile screenshots ===");
  const indexPath = path.join(WORKSPACE, "accounts_index.md");
  let index = await fs.readFile(indexPath, "utf8");
  const rows = [];

  for (const c of unique.slice(0, 8)) {
    const dir = path.join(WORKSPACE, "accounts", c.handle_dir);
    await fs.mkdir(dir, { recursive: true });
    const shotPath = path.join(dir, "profile.png");
    console.log(`Screenshot: ${c.profile_url}`);
    await callTool(client, "browser_navigate", { url: c.profile_url });
    const out = await callTool(client, "browser_take_screenshot", {
      filename: shotPath,
      type: "png",
    });
    if (/Error/i.test(out)) console.log("  warn:", out.slice(0, 120));
    else console.log("  saved:", shotPath);
    rows.push(
      `| ${c.platform} | ${c.profile_url} | ${c.handle_dir} | HARVESTED | ${c.profile_url} |`
    );
  }

  // Rewrite accounts table
  const headerEnd = index.indexOf("| instagram |");
  if (headerEnd >= 0) {
    const prefix = index.slice(0, headerEnd);
    index = prefix + rows.join("\n") + "\n\n## Discovery log\n\n" +
      `- Subject: ${SUBJECT}\n- Reference: ${REFERENCE}\n- Candidates harvested: ${rows.length}\n`;
    await fs.writeFile(indexPath, index);
  }

  await client.close();
  console.log("\nDone. Candidates:", unique.length);
  for (const c of unique) console.log(`  ${c.platform}: ${c.profile_url}`);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
