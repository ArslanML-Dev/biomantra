// Screenshot every page at phone and laptop size with headless Chromium (Playwright).
// Needs the backend (8000) and website (5173) running, e.g. via start_demo.ps1.
// Usage (from frontend/):  node scripts/screenshots.mjs [outDir] [adminToken]
import { chromium } from "playwright";
import { mkdirSync } from "node:fs";

const BASE = "http://localhost:5173";
const OUT = process.argv[2] ?? "../docs/evidence/screens";
const TOKEN = process.argv[3] ?? "change-me";
const USER = { id: 1, name: "Aarav Sharma", institution_id: 1, institution: "CSE-DS" };
const SIZES = {
  phone: { viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true },
  laptop: { viewport: { width: 1366, height: 768 } },
};
// [file name, path, localStorage to set, extra step]
const PAGES = [
  ["01_user_picker", "/", {}],
  ["02_home_en", "/", { user: USER, lang: "en" }],
  ["03_home_hi", "/", { user: USER, lang: "hi" }],
  ["04_act_website", "/act", { user: USER }],
  ["05_leaderboard_institutions", "/leaderboard", { user: USER }],
  ["06_leaderboard_users", "/leaderboard", { user: USER }, (p) => p.getByRole("button", { name: "Users" }).click()],
  ["07_map", "/map", { user: USER }],
  ["08_admin_login", "/admin", { user: USER }],
  ["09_admin_queue", "/admin", { user: USER, adminToken: TOKEN }],
  ["10_about", "/about", { user: USER }],
  ["11_settings", "/settings", { user: USER }],
];

const LONG = ["09_admin_queue", "10_about"];

/** Open one page with the given storage, wait for data, and save a full-page screenshot. */
async function shoot(browser, size, [name, path, storage, step]) {
  const context = await browser.newContext(SIZES[size]);
  await context.addInitScript((s) => {
    localStorage.clear();
    sessionStorage.clear();
    if (s.user) localStorage.setItem("user", JSON.stringify(s.user));
    if (s.lang) localStorage.setItem("lang", s.lang);
    if (s.adminToken) sessionStorage.setItem("adminToken", s.adminToken);
  }, storage);
  const page = await context.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto(BASE + path, { waitUntil: "networkidle", timeout: 90000 });
  if (step) { await step(page); await page.waitForLoadState("networkidle"); }
  await page.waitForTimeout(1500); // let map tiles and fonts settle
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  const files = [`${size}_${name}.png`];
  // Phone: exactly what the screen shows. Laptop and long phone pages: whole page, with the fixed
  // bottom bar moved to the end so it does not cover content in the stitched image.
  const full = size === "laptop" || LONG.includes(name);
  if (size === "phone") await page.screenshot({ path: `${OUT}/${files[0]}` });
  if (full) {
    await page.addStyleTag({ content: ".bottomnav{position:static!important}" });
    const file = size === "phone" ? `${size}_${name}_full.png` : files[0];
    await page.screenshot({ path: `${OUT}/${file}`, fullPage: true });
    if (size === "phone") files.push(file);
  }
  await context.close();
  return { file: files.join(" + "), overflowPx: overflow, errors };
}

mkdirSync(OUT, { recursive: true });
const browser = await chromium.launch({ headless: true });
for (const size of Object.keys(SIZES)) {
  for (const spec of PAGES) {
    const r = await shoot(browser, size, spec);
    console.log(`${r.file}${r.overflowPx > 0 ? `  !! horizontal overflow ${r.overflowPx}px` : ""}${r.errors.length ? `  !! errors: ${r.errors.join("; ")}` : ""}`);
  }
}
await browser.close();
