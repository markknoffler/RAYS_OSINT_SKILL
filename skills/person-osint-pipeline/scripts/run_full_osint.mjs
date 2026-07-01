#!/usr/bin/env node
/**
 * Full OSINT discovery via Playwright MCP HTTP (headed Chrome).
 * Agent session driver — uses MCP tools only, not standalone Playwright.
 */
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";
import fs from "node:fs/promises";
import path from "node:path";

const MCP_URL = process.env.PLAYWRIGHT_MCP_URL || "http://localhost:8931/mcp";
const WORKSPACE =
  process.env.WORKSPACE ||
  "/home/mark/Desktop/RAYSpy/test_investigation/samreedh_bhuyan_osint";
const REFERENCE =
  process.env.REFERENCE_PHOTO ||
  `${WORKSPACE}/reference.jpg`;
const SUBJECT = "Samreedh Bhuyan";

async function callTool(client, name, args = {}) {
  const result = await client.callTool({ name, arguments: args });
  const text = result.content
    ?.map((c) => (c.type === "text" ? c.text : JSON.stringify(c)))
    .join("\n");
  return text || "";
}

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

function extractUrls(text, patterns) {
  const found = new Set();
  for (const re of patterns) {
    for (const m of text.matchAll(re)) {
      let u = m[0];
      if (!u.startsWith("http")) u = `https://${u}`;
      try {
        const parsed = new URL(u.split("?")[0].split("#")[0]);
        if (!parsed.hostname.includes(".")) continue;
        found.add(parsed.origin + parsed.pathname);
      } catch {
        /* skip malformed */
      }
    }
  }
  return [...found];
}

function slugFromUrl(url) {
  return url
    .replace(/^https?:\/\//, "")
    .replace(/[^a-zA-Z0-9]+/g, "_")
    .slice(0, 80);
}

function handleFromUrl(url, platform) {
  const u = new URL(url);
  const segs = u.pathname.split("/").filter(Boolean);
  let handle = segs[segs.length - 1] || "unknown";
  if (platform === "linkedin" && segs[0] === "in") handle = segs[1] || handle;
  const suffix = {
    instagram: "ig",
    linkedin: "linkedin",
    x: "x",
    facebook: "fb",
    github: "github",
  }[platform];
  return suffix && !handle.endsWith(`_${suffix}`) ? `${handle}_${suffix}` : handle;
}

async function googleSearch(client, query) {
  await callTool(client, "browser_navigate", {
    url: `https://www.google.com/search?q=${encodeURIComponent(query)}`,
  });
  await sleep(2500);
  return callTool(client, "browser_snapshot", {});
}

async function main() {
  const transport = new StreamableHTTPClientTransport(new URL(MCP_URL));
  const client = new Client({ name: "person-osint-full", version: "1.0.0" });
  await client.connect(transport);

  await fs.mkdir(path.join(WORKSPACE, "articles"), { recursive: true });
  await fs.mkdir(path.join(WORKSPACE, "accounts"), { recursive: true });

  const candidates = [];
  const articles = [];

  const searches = [
    { platform: "linkedin", query: `site:linkedin.com/in "${SUBJECT}"` },
    { platform: "instagram", query: `site:instagram.com "${SUBJECT}"` },
    { platform: "x", query: `site:x.com "${SUBJECT}" OR site:twitter.com "${SUBJECT}"` },
    { platform: "facebook", query: `site:facebook.com "${SUBJECT}"` },
    { platform: "github", query: `site:github.com "${SUBJECT}" OR markknoffler` },
    { platform: "youtube", query: `site:youtube.com "${SUBJECT}"` },
    { platform: "web", query: `"${SUBJECT}" KIIT Bhubaneswar` },
    { platform: "article", query: `"${SUBJECT}" hackathon OR interview OR article OR award` },
    { platform: "article", query: `"${SUBJECT}" CSIR OR ProfAI OR rays-core OR PyPI` },
    { platform: "web", query: `"${SUBJECT}"` },
  ];

  const urlPatterns = {
    linkedin: [/linkedin\.com\/in\/[a-zA-Z0-9_-]+/gi],
    instagram: [/instagram\.com\/[a-zA-Z0-9_.]+/gi],
    x: [/(?:x|twitter)\.com\/[a-zA-Z0-9_]+/gi],
    facebook: [/facebook\.com\/[a-zA-Z0-9.]+/gi],
    github: [/github\.com\/[a-zA-Z0-9_-]+(?:\/[a-zA-Z0-9_.-]+)?/gi],
    youtube: [/youtube\.com\/(?:@|channel\/|c\/)[a-zA-Z0-9_-]+/gi],
    web: [
      /pypi\.org\/project\/[a-zA-Z0-9_-]+/gi,
      /github\.com\/[a-zA-Z0-9_-]+\/[a-zA-Z0-9_.-]+/gi,
      /linkedin\.com\/in\/[a-zA-Z0-9_-]+/gi,
    ],
    article: [
      /pypi\.org\/project\/[a-zA-Z0-9_-]+/gi,
      /github\.com\/[a-zA-Z0-9_-]+\/[a-zA-Z0-9_.-]+/gi,
      /linkedin\.com\/posts\/[a-zA-Z0-9_-]+[^"\s]*/gi,
      /hackathon[^"\s]*/gi,
    ],
  };

  console.log("=== Phase 1: Discovery ===");
  for (const { platform, query } of searches) {
    console.log(`Search: ${query}`);
    const snap = await googleSearch(client, query);
    const patterns = urlPatterns[platform] || [/https?:\/\/[^\s"<>]+/gi];
    for (const url of extractUrls(snap, patterns)) {
      if (/google\.|gstatic|youtube\.com\/results|\/share|\/intent|\/login/.test(url))
        continue;
      const plat = url.includes("linkedin")
        ? "linkedin"
        : url.includes("instagram")
          ? "instagram"
          : url.includes("x.com") || url.includes("twitter")
            ? "x"
            : url.includes("facebook")
              ? "facebook"
              : url.includes("github")
                ? "github"
                : url.includes("pypi")
                  ? "pypi"
                  : url.includes("youtube")
                    ? "youtube"
                    : platform;
      const entry = {
        platform: plat,
        profile_url: url,
        handle_dir:
          plat === "pypi"
            ? slugFromUrl(url)
            : handleFromUrl(url, plat),
      };
      if (plat === "article" || plat === "web" || plat === "pypi") {
        articles.push(entry);
      } else {
        candidates.push(entry);
      }
    }
  }

  // Known high-confidence profiles
  candidates.push(
    {
      platform: "linkedin",
      profile_url: "https://www.linkedin.com/in/samreedh-bhuyan",
      handle_dir: "samreedh-bhuyan_linkedin",
    },
    {
      platform: "github",
      profile_url: "https://github.com/markknoffler",
      handle_dir: "markknoffler_github",
    }
  );
  articles.push(
    {
      platform: "pypi",
      profile_url: "https://pypi.org/project/rays-core/",
      handle_dir: "pypi_rays_core",
    },
    {
      platform: "github",
      profile_url: "https://github.com/markknoffler/RAYS-CORE-CLI",
      handle_dir: "github_rays_core_cli",
    }
  );

  const dedupe = (arr) => {
    const seen = new Set();
    return arr.filter((c) => {
      if (seen.has(c.profile_url)) return false;
      seen.add(c.profile_url);
      return true;
    });
  };
  const uniqueCandidates = dedupe(candidates);
  const uniqueArticles = dedupe(articles);

  console.log("\n=== Phase 1a: Reverse image search ===");
  await callTool(client, "browser_navigate", { url: "https://www.google.com/imghp" });
  await sleep(1500);
  const imgSnap = await callTool(client, "browser_snapshot", {});
  if (/Search by image|camera|upload/i.test(imgSnap)) {
    console.log("Google Images ready — attempting upload");
    // click camera if ref available would need snapshot refs; try direct lens URL
    await callTool(client, "browser_navigate", {
      url: "https://lens.google.com/search?p",
    });
    await sleep(2000);
    try {
      await callTool(client, "browser_file_upload", { paths: [REFERENCE] });
      await sleep(4000);
      const lensSnap = await callTool(client, "browser_snapshot", {});
      for (const url of extractUrls(lensSnap, [
        /linkedin\.com\/in\/[a-zA-Z0-9_-]+/gi,
        /instagram\.com\/[a-zA-Z0-9_.]+/gi,
        /github\.com\/[a-zA-Z0-9_-]+/gi,
      ])) {
        uniqueCandidates.push({
          platform: url.includes("linkedin") ? "linkedin" : url.includes("instagram") ? "instagram" : "github",
          profile_url: url,
          handle_dir: handleFromUrl(url, url.includes("linkedin") ? "linkedin" : "github"),
        });
      }
    } catch (e) {
      console.log("Reverse image upload skipped:", e.message);
    }
  }

  console.log("\n=== Phase 2: Screenshot harvest ===");
  const rows = [];
  for (const c of uniqueCandidates.slice(0, 10)) {
    const dir = path.join(WORKSPACE, "accounts", c.handle_dir);
    await fs.mkdir(dir, { recursive: true });
    const shotPath = path.join(dir, "profile.png");
    console.log(`Harvest: ${c.profile_url}`);
    await callTool(client, "browser_navigate", { url: c.profile_url });
    await sleep(3000);
    await callTool(client, "browser_take_screenshot", {
      filename: shotPath,
      type: "png",
    });
    rows.push(
      `| ${c.platform} | ${c.profile_url} | ${c.handle_dir} | HARVESTED | ${c.profile_url} |`
    );
  }

  console.log("\n=== Phase 1d: Article harvest ===");
  const articleRows = [];
  for (const a of uniqueArticles.slice(0, 8)) {
    const slug = a.handle_dir || slugFromUrl(a.profile_url);
    const mdPath = path.join(WORKSPACE, "articles", `${slug}.md`);
    const pngPath = path.join(WORKSPACE, "articles", `${slug}.png`);
    console.log(`Article: ${a.profile_url}`);
    await callTool(client, "browser_navigate", { url: a.profile_url });
    await sleep(2500);
    const snap = await callTool(client, "browser_snapshot", {});
    await callTool(client, "browser_take_screenshot", {
      filename: pngPath,
      type: "png",
    });
    const excerpt = snap.slice(0, 4000);
    await fs.writeFile(
      mdPath,
      `# ${slug}\n\n**URL:** ${a.profile_url}\n**Platform:** ${a.platform}\n\n## Extracted\n\n${excerpt}\n`
    );
    articleRows.push(`| ${a.platform} | ${a.profile_url} | ${slug} | HARVESTED |`);
  }

  const indexPath = path.join(WORKSPACE, "accounts_index.md");
  const header = `# Accounts Index

**Subject workspace:** \`${WORKSPACE}\`

**Authorized by:** Self (Samreedh Bhuyan)
**Purpose:** Self-investigation skill test
**Subject:** Samreedh Bhuyan

## Accounts

| platform | profile_url | handle_dir | verification_status | image_links |
| --- | --- | --- | --- | --- |
`;
  await fs.writeFile(indexPath, header + rows.join("\n") + "\n");

  const articlesIndex = `# Articles & Web Findings

| platform | url | slug | status |
| --- | --- | --- | --- |
${articleRows.join("\n")}
`;
  await fs.writeFile(path.join(WORKSPACE, "articles_index.md"), articlesIndex);

  await client.close();
  console.log("\nDone.", uniqueCandidates.length, "candidates,", uniqueArticles.length, "articles");
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
