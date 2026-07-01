#!/usr/bin/env node
/**
 * Opens Firefox with a PERSISTENT profile and keeps it alive for login.
 * NOT for investigations — use Playwright MCP for that after logging in here.
 *
 * Why this exists: MCP server closes the browser when the agent disconnects (~2s).
 * This script uses Playwright directly so the window stays open 20 minutes.
 *
 * Profile is shared with MCP (--user-data-dir same path) — logins persist forever.
 */
import { firefox } from "playwright";
import { mkdir } from "node:fs/promises";

const PROFILE = process.env.PLAYWRIGHT_OSINT_PROFILE ||
  `${process.env.HOME}/.cursor/playwright-osint-profile`;
const MINUTES = Number(process.env.LOGIN_MINUTES || "20");
const MS = MINUTES * 60 * 1000;

async function main() {
  await mkdir(PROFILE, { recursive: true });

  console.log("");
  console.log("=".repeat(60));
  console.log("  OSINT Login Browser — stays open", MINUTES, "minutes");
  console.log("=".repeat(60));
  console.log("  Profile (persistent):", PROFILE);
  console.log("");
  console.log("  1. Log into LinkedIn in tab 1");
  console.log("  2. Log into Instagram in tab 2");
  console.log("  3. Leave this terminal running — do NOT close the browser");
  console.log("  4. When done, wait for auto-close or press Ctrl+C");
  console.log("");
  console.log("  Sessions are saved. Future MCP runs reuse this profile.");
  console.log("=".repeat(60));
  console.log("");

  const context = await firefox.launchPersistentContext(PROFILE, {
    headless: false,
    viewport: { width: 1280, height: 900 },
    ignoreHTTPSErrors: true,
  });

  const linkedin = context.pages()[0] || (await context.newPage());
  await linkedin.goto("https://www.linkedin.com/login", {
    waitUntil: "domcontentloaded",
    timeout: 60000,
  });

  const insta = await context.newPage();
  await insta.goto("https://www.instagram.com/accounts/login/", {
    waitUntil: "domcontentloaded",
    timeout: 60000,
  });

  console.log(`Browser open. Closing in ${MINUTES} minutes...`);
  console.log("(Press Ctrl+C to close early — login state is already saved to disk.)");
  console.log("");

  await new Promise((resolve) => {
    const timer = setTimeout(resolve, MS);
    process.on("SIGINT", () => {
      clearTimeout(timer);
      resolve();
    });
    process.on("SIGTERM", () => {
      clearTimeout(timer);
      resolve();
    });
  });

  await context.close();
  console.log("Login browser closed. Profile saved at:", PROFILE);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
