#!/usr/bin/env node
/**
 * Poll for CAPTCHA clearance while keeping MCP session + browser alive.
 * Implements backoff: 60s, 60s, then 120s, 240s, 480s, ...
 * Usage: node poll_captcha.mjs [max_rounds]
 */
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";

const CAPTCHA_SIGNALS = [
  /\/sorry\//i,
  /unusual traffic/i,
  /i'm not a robot/i,
  /verify you're human/i,
  /just a moment/i,
  /security check/i,
];

function isCaptcha(text, url = "") {
  const hay = `${url}\n${text}`;
  return CAPTCHA_SIGNALS.some((re) => re.test(hay));
}

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

const maxRounds = Number(process.argv[2] || 999);
const c = new Client({ name: "captcha-poll", version: "1.0.0" });
await c.connect(new StreamableHTTPClientTransport(new URL("http://localhost:8931/mcp")));

let waitSec = 60;
let round = 0;

while (round < maxRounds) {
  round++;
  const snap = await c.callTool({ name: "browser_snapshot", arguments: {} });
  const text = snap.content?.map((x) => (x.type === "text" ? x.text : "")).join("\n") || "";
  const urlMatch = text.match(/Page URL: (.+)/);
  const url = urlMatch?.[1] || "";

  if (!isCaptcha(text, url)) {
    console.log(`CAPTCHA_CLEAR round=${round} url=${url}`);
    console.log(text.slice(0, 2000));
    await c.close();
    process.exit(0);
  }

  console.log(`CAPTCHA_WAIT round=${round} wait_sec=${waitSec} url=${url}`);
  console.log("Solve CAPTCHA in the visible browser window. Agent is waiting...");

  // Keep MCP connection open during wait (browser stays alive via daemon)
  await sleep(waitSec * 1000);

  // After 2nd wait at 60s, double subsequent waits
  if (round >= 2) waitSec = Math.min(waitSec * 2, 3600);
}

console.error("CAPTCHA still present after max rounds");
await c.close();
process.exit(1);
