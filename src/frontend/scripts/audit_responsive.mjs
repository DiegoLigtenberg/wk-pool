/**
 * UI/UX responsive smoke audit (Playwright).
 *
 * Usage:
 *   npm i -D playwright
 *   npx playwright install chromium
 *   npm run build && npm run preview -- --host 127.0.0.1 --port 4173
 *   APP_URL=http://127.0.0.1:4173/ node scripts/audit_responsive.mjs
 */
import { chromium } from "playwright";

const URL = process.env.APP_URL ?? "http://127.0.0.1:4173/";

const VIEWPORTS = [
  { name: "mobile", width: 390, height: 844, isMobile: true, hasTouch: true },
  { name: "tablet", width: 834, height: 1194, isMobile: true, hasTouch: true },
  { name: "desktop", width: 1440, height: 900, isMobile: false, hasTouch: false },
];

async function pageOverflow(page) {
  return page.evaluate(() => {
    const doc = document.documentElement;
    return {
      scrollWidth: doc.scrollWidth,
      clientWidth: doc.clientWidth,
      horizontalOverflow: doc.scrollWidth > doc.clientWidth + 2,
    };
  });
}

async function auditViewport(browser, vp) {
  const context = await browser.newContext({
    viewport: { width: vp.width, height: vp.height },
    isMobile: vp.isMobile,
    hasTouch: vp.hasTouch,
    deviceScaleFactor: vp.isMobile ? 2 : 1,
  });
  const page = await context.newPage();
  const issues = [];

  try {
    await page.goto(URL, { waitUntil: "networkidle", timeout: 25000 });
    await page.locator(".app-shell").waitFor({ timeout: 10000 });
  } catch (error) {
    issues.push(`load failed: ${error.message}`);
    await context.close();
    return { viewport: vp.name, width: vp.width, issues };
  }

  const overflow = await pageOverflow(page);
  if (overflow.horizontalOverflow) {
    issues.push(`page horizontal overflow (${overflow.scrollWidth}px > ${overflow.clientWidth}px)`);
  }

  await page.getByRole("button", { name: /Wedstrijden/i }).click();
  await page.locator("#wedstrijden").waitFor();

  const firstScore = page.locator(".fixture-row .result-pill").first();
  if (!(await firstScore.count())) {
    issues.push("no fixture score pills found");
  } else {
    await firstScore.click();
    const panels = page.locator(".prediction-panel");
    if ((await panels.count()) !== 1) {
      issues.push(`expected 1 prediction panel after score tap, got ${await panels.count()}`);
    } else {
      const panelBox = await panels.first().boundingBox();
      const vpSize = page.viewportSize();
      if (panelBox && vpSize && panelBox.width > vpSize.width + 2) {
        issues.push(`prediction panel wider than viewport (${Math.round(panelBox.width)}px)`);
      }
    }

    await page.locator("#wedstrijden h2").click();
    if ((await panels.count()) !== 0) {
      issues.push("outside click did not close prediction panel");
    }

    const rows = page.locator(".fixture-row");
    if ((await rows.count()) >= 2) {
      await rows.nth(0).locator(".result-pill").click();
      await rows.nth(1).locator(".result-pill").click();
      if ((await panels.count()) !== 1) {
        issues.push(`singleton panel failed when switching rows (${await panels.count()} open)`);
      }
      await page.locator("#wedstrijden h2").click();
    }
  }

  if (vp.hasTouch) {
    const aiBtn = page.locator(".ai-marker-button").first();
    if (await aiBtn.count()) {
      const box = await aiBtn.boundingBox();
      if (box && (box.width < 40 || box.height < 40)) {
        issues.push(`AI badge tap target < 40px (${Math.round(box.width)}×${Math.round(box.height)})`);
      }
    }
    const interactiveCell = page.locator(".match-cell--interactive").first();
    if (await interactiveCell.count()) {
      const styles = await interactiveCell.evaluate((el) => getComputedStyle(el).touchAction);
      if (styles !== "manipulation") {
        issues.push(`match-cell touch-action is "${styles}", expected manipulation`);
      }
    }
  }

  await page.getByRole("button", { name: /Knock-out/i }).click();
  const bracket = page.locator(".knockout-bracket-shell");
  if (await bracket.count()) {
    const bracketMetrics = await bracket.evaluate((el) => ({
      scrollWidth: el.scrollWidth,
      clientWidth: el.clientWidth,
    }));
    if (bracketMetrics.scrollWidth > bracketMetrics.clientWidth + 4) {
      // intentional horizontal scroll container on narrow viewports
      if (!overflow.horizontalOverflow) {
        issues.push(
          `knockout uses inner scroll (${bracketMetrics.scrollWidth}/${bracketMetrics.clientWidth}px), OK if page does not overflow`,
        );
      }
    }
    const knockoutOverflow = await pageOverflow(page);
    if (knockoutOverflow.horizontalOverflow) {
      issues.push("page horizontal overflow on knockout view");
    }
  }

  await page.getByRole("button", { name: /Wedstrijden/i }).click();
  const teamBtn = page.locator(".team-label-button").first();
  if (await teamBtn.count()) {
    await teamBtn.click();
    const modal = page.locator('[role="dialog"]');
    if (!(await modal.count())) {
      issues.push("team insight modal did not open");
    } else {
      const modalBox = await modal.boundingBox();
      const vpSize = page.viewportSize();
      if (modalBox && vpSize && modalBox.width > vpSize.width + 2) {
        issues.push("team modal wider than viewport");
      }
      await page.keyboard.press("Escape");
    }
  }

  await context.close();
  return { viewport: vp.name, width: vp.width, issues, overflow };
}

const browser = await chromium.launch({ channel: "chrome", headless: true });
const results = [];
for (const vp of VIEWPORTS) {
  results.push(await auditViewport(browser, vp));
}
await browser.close();

const failed = results.filter((r) => r.issues.some((i) => !i.includes("OK if")));
console.log(JSON.stringify(results, null, 2));
if (failed.length) {
  console.error(`\n${failed.length} viewport(s) with issues`);
  process.exit(1);
}
console.log("\nAll viewports passed responsive smoke checks.");
