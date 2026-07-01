# Playwright MCP → OSINT task map

**There is no `browser_scroll`.** Scroll the page like a human using the tools below.

| OSINT task | MCP tool(s) | How |
|------------|-------------|-----|
| Open a URL | `browser_navigate` | `{ "url": "..." }` |
| Read page / get click refs | `browser_snapshot` | Always before click/type; CAPTCHA check here |
| Google subject name (human) | `browser_navigate` → `google.com` → `browser_click` search box → `browser_type` `{text, submit:true}` | **Do not** start with `site:linkedin` dorks in Session 1 |
| Click a search result | `browser_click` | Use `target: "eN"` ref from snapshot |
| Scroll down | `browser_press_key` | `{ "key": "PageDown" }` or `ArrowDown` repeatedly |
| Scroll to bottom | `browser_press_key` | `{ "key": "End" }` |
| Scroll up | `browser_press_key` | `{ "key": "PageUp" }` |
| Full page capture | `browser_take_screenshot` | `{ "fullPage": true, "filename": "..." }` |
| Viewport screenshot | `browser_take_screenshot` | `{ "filename": "...", "type": "png" }` |
| Upload reference photo | `browser_file_upload` | Reverse image on Google Images |
| Open link in new tab | `browser_tabs` | `{ "action": "new", "url": "..." }` |
| Go back to Google results | `browser_navigate_back` | After finishing one hit |
| Next Google results page | `browser_click` | "Next" link ref from snapshot |
| Wait for lazy load | `browser_wait_for` | `{ "text": "..." }` or time |
| Expand "Load more" / "Show all" | `browser_click` | Ref from snapshot |
| Fill login form | `browser_fill_form` / `browser_type` | Human-in-the-loop preferred |
| Hover menu | `browser_hover` | Dropdowns |
| Handle popup | `browser_handle_dialog` | `{ "accept": true }` |
| Pixel scroll (vision cap) | `browser_mouse_wheel` | Requires `--caps=vision` |

## Scroll pattern (LinkedIn / Instagram / long pages)

```
loop until no new content in snapshot:
  browser_press_key PageDown
  browser_wait_for (2–3 s)
  browser_snapshot → read posts / CAPTCHA
  browser_take_screenshot (optional per post)
  browser_click on post if thumbnail needs full view
```

| CAPTCHA gate | `poll_captcha.mjs` or `browser_wait_for` + `browser_snapshot` | Keep browser open; 60s→60s→double backoff |

**CAPTCHA signals:** URL `/sorry/`; snapshot text `I'm not a robot`, `unusual traffic`, `verify you're human`.  
**Do not** match the word "robot" in normal post text.
