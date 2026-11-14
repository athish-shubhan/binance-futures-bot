// Records docs/demo.gif from the real web UI.
//
//   python scripts/demo_server.py 5080 &     (UI with a canned exchange reply, no keys)
//   node scripts/record_demo.js               (needs Playwright and ffmpeg)
const { chromium } = require("playwright");
const { execFileSync } = require("node:child_process");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

const URL = process.env.DEMO_URL || "http://127.0.0.1:5080/";
const OUT = path.resolve(__dirname, "..", "docs", "demo.gif");
const SIZE = { width: 1100, height: 800 };

(async () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "bot-demo-"));
  const browser = await chromium.launch();
  const context = await browser.newContext({ viewport: SIZE, recordVideo: { dir, size: SIZE } });
  const page = await context.newPage();
  const pause = (ms) => page.waitForTimeout(ms);
  const type = async (sel, text) => { await page.click(sel); await page.fill(sel, ""); await page.type(sel, text, { delay: 110 }); };
  await page.goto(URL);
  await pause(1200);

  // 1. Market buy.
  await type("#qty", "0.001");
  await pause(600);
  await page.click("#submit-btn");
  await pause(2200);

  // 2. Limit sell: the price field appears with the order type.
  await page.click("#btn-sell");
  await pause(500);
  await page.selectOption("#order-type", "LIMIT");
  await pause(600);
  await type("#qty", "0.002");
  await type("#price", "99000");
  await pause(600);
  await page.click("#submit-btn");
  await pause(2200);

  // 3. Stop-market with the stop price left empty: rejected before any request.
  await page.selectOption("#order-type", "STOP_MARKET");
  await pause(700);
  await page.click("#submit-btn");
  await pause(2400);

  await context.close();
  await browser.close();
  const video = path.join(dir, fs.readdirSync(dir).find((f) => f.endsWith(".webm")));
  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  execFileSync("ffmpeg", ["-y", "-loglevel", "error", "-i", video, "-vf",
    "fps=8,scale=820:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=64[p];[b][p]paletteuse=dither=none:diff_mode=rectangle", OUT]);
  fs.rmSync(dir, { recursive: true, force: true });
  console.log("wrote", OUT, (fs.statSync(OUT).size / 1e6).toFixed(1) + " MB");
})();
