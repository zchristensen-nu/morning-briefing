// A PR person's morning in the briefing editor: edit every line, press Enter everywhere, paste
// from Word and the web, add/remove/reorder stories, reload, copy for Outlook.
// Needs Playwright (npm i -g playwright && npx playwright install). macOS keys (⌘).
//   python3 render_page.py briefings/<a date with 11+ stories>.md > /tmp/page.html
//   node tests/editor.mjs /tmp/page.html chromium   # or webkit, firefox
import { chromium, webkit, firefox } from "playwright";
const [file, engine = "chromium"] = process.argv.slice(2);
const browser = await ({ chromium, webkit, firefox })[engine].launch();
const ctx = await browser.newContext({ viewport: { width: 1400, height: 900 } });
const p = await ctx.newPage();
const errors = [];
p.on("pageerror", e => errors.push(e.message));
let fails = 0;
const ok = (cond, msg) => { console.log((cond ? "  ok   " : "  FAIL ") + msg); if (!cond) fails++; };
const url = "file://" + file;

// Copy → capture what would reach Outlook.
await p.addInitScript(() => {
  window.__copied = null; window.__opened = null;
  navigator.clipboard.write = async items => { window.__copied = await (await items[0].getType("text/html")).text(); };
  window.open = u => { window.__opened = u; };
  window.confirm = () => true;
});
await p.goto(url);
const n = () => p.evaluate(() => document.querySelectorAll("#briefing [data-entry]").length);
const story = i => p.locator("#briefing [data-entry]").nth(i);
const f = (i, kind) => story(i).locator(`[data-f="${kind}"]`);
const active = () => p.evaluate(() => { const a = document.activeElement; return a?.dataset?.f ? a.dataset.f + ":" + [...document.querySelectorAll("#briefing [data-entry]")].indexOf(a.closest("[data-entry]")) : a?.tagName; });
const txt = l => l.evaluate(e => e.textContent);
const html = l => l.evaluate(e => e.innerHTML);
const end = async l => { await l.click(); await p.keyboard.press(engine === "webkit" ? "Meta+ArrowRight" : "End"); await l.evaluate(e => { const r = document.createRange(); r.selectNodeContents(e); r.collapse(false); const s = getSelection(); s.removeAllRanges(); s.addRange(r); }); };
// Real copy + paste: put the text on the page, select it, ⌘C, then ⌘V into the field
// (keeps the caret where the test left it).
const paste = async (l, plain, rich) => {
  const sel = await l.evaluate(e => { const s = getSelection(); return s.rangeCount && e.contains(s.anchorNode) ? null : "start"; });
  await p.evaluate(([plain, rich]) => {
    const keep = getSelection().rangeCount ? getSelection().getRangeAt(0).cloneRange() : null;
    window.__keep = keep;
    const d = document.createElement("div"); d.id = "__src"; d.style.cssText = "position:fixed;left:0;top:0;opacity:.01;white-space:pre";
    if (rich) d.innerHTML = rich; else d.textContent = plain;
    document.body.append(d);
    const r = document.createRange(); r.selectNodeContents(d); const s = getSelection(); s.removeAllRanges(); s.addRange(r);
  }, [plain, rich]);
  await p.keyboard.press("Meta+c");
  await l.evaluate((e, sel) => {
    document.getElementById("__src").remove();
    e.focus();
    const s = getSelection(); s.removeAllRanges();
    if (window.__keep && e.contains(window.__keep.startContainer)) s.addRange(window.__keep);
    else { const r = document.createRange(); r.selectNodeContents(e); r.collapse(false); s.addRange(r); }
  }, sel);
  await p.keyboard.press("Meta+v");
};
const N0 = await n();

console.log(`\n[${engine}] load`);
ok(N0 >= 11, `the page has enough stories to test (${N0})`);
ok(await p.locator("#briefing [data-f]").count() === N0 * 3 + 2, "every story has outlet, headline and summary fields (+ title, tagline)");
const pristine = await p.evaluate(() => clean(sheet).innerHTML);
const staticSheet = await (async () => { const q = await ctx.newPage(); await q.route("**/*", r => r.continue()); await q.setContent((await (await import("fs")).promises.readFile(file, "utf8")).replace(/<script>[\s\S]*?<\/script>/g, "")); const h = await q.evaluate(() => document.getElementById("briefing").innerHTML); await q.close(); return h; })();
ok(pristine === staticSheet, "copy of an untouched draft is byte-identical to the rendered email");

console.log(`[${engine}] Enter never breaks a story`);
const head0 = await txt(f(0, "head")), sum0 = await txt(f(0, "sum"));
await end(f(0, "outlet")); await p.keyboard.press("Enter");
ok(await active() === "head:0", "Enter in outlet → headline");
await p.keyboard.press("Enter");
ok(await active() === "sum:0", "Enter in headline → summary");
await f(0, "sum").click({ position: { x: 40, y: 5 } });
for (let i = 0; i < 3; i++) { await p.keyboard.press("Shift+Enter"); }
ok(await n() === N0 && !(await html(f(0, "sum"))).includes("<br"), "Shift+Enter in the middle of a summary adds nothing");
await end(f(0, "sum")); await p.keyboard.press("Enter");
ok(await p.locator(".slot input").isVisible() && await n() === N0, "Enter at a summary's end opens 'add a story', no new story");
await p.keyboard.press("Escape");
ok(await p.locator(".slot").count() === 0 && await active() === "sum:0", "Esc closes it and returns to the summary");
ok(await txt(f(0, "head")) === head0 && await txt(f(0, "sum")) === sum0, "headline and summary text untouched");

console.log(`[${engine}] typing and formatting`);
await end(f(1, "sum")); await p.keyboard.type(" Extra detail.");
ok((await txt(f(1, "sum"))).endsWith("Extra detail."), "typing appends to the summary");
await p.keyboard.press("Meta+b"); await p.keyboard.type(" X"); await p.keyboard.press("Meta+i"); await p.keyboard.type("Y");
ok(!/<(b|i|strong|em)\b/.test(await html(f(1, "sum"))), "⌘B / ⌘I don't add bold or italic");
await f(1, "sum").click(); await p.keyboard.press("Meta+a"); await p.keyboard.press("Backspace");
ok(await html(f(1, "sum")) === "", "select-all + delete empties just that summary");
ok(await f(1, "sum").evaluate(e => /summary|attr\(data-ph\)/.test(getComputedStyle(e, "::before").content)), "empty summary shows its placeholder");
ok(await txt(f(1, "head")) !== "" && await n() === N0, "headline and story count survive");
await p.keyboard.type("New summary written by hand.");
ok(await txt(f(1, "sum")) === "New summary written by hand.", "typing into the emptied summary works");
await f(1, "sum").evaluate(e => { const r = document.createRange(); r.selectNodeContents(e); r.collapse(true); const s = getSelection(); s.removeAllRanges(); s.addRange(r); }); await p.keyboard.press("Backspace");
ok(await txt(f(1, "head")) !== "" && await txt(f(1, "sum")) === "New summary written by hand.", "Backspace at a summary's start never merges into the headline");

console.log(`[${engine}] paste`);
await end(f(2, "sum"));
await paste(f(2, "sum"), "", "<p style='color:red'><b>Pasted</b></p><p>from   Word</p><p>with breaks</p>");
const s2 = await html(f(2, "sum"));
ok(s2.includes("Pasted from Word with breaks") && !/<(p|b|br|div|span)\b/.test(s2), "rich, multi-line paste lands as one plain line");
const oldHref = await story(3).locator("a").getAttribute("href");
await f(3, "head").click();
await paste(f(3, "head"), "https://example.com/news/2026/10/27/new-link");
ok((await story(3).locator("a").getAttribute("href")) === "https://example.com/news/2026/10/27/new-link" && oldHref !== "https://example.com/news/2026/10/27/new-link", "a link pasted on a headline replaces its link");
ok(await n() === N0, "…without adding a story");
await end(f(4, "sum"));
await paste(f(4, "sum"), "https://www.insidehighered.com/news/2026/10/27/some-new-story");
ok(await n() === N0 + 1, "a link pasted in a summary adds a story");
ok(await story(5).locator("a").getAttribute("href") === "https://www.insidehighered.com/news/2026/10/27/some-new-story", "…right after the story you were in");
ok(await active() === "sum:5", "…with its summary ready to type");
await p.keyboard.type("Summary for the added story.");
ok(await txt(f(5, "sum")) === "Summary for the added story.", "typing replaces the summary placeholder");

console.log(`[${engine}] add from the + box`);
await end(f(5, "sum")); await p.keyboard.press("Enter");
await p.locator(".slot input").fill("https://www.nytimes.com/2026/10/27/us/another-story.html"); await p.keyboard.press("Enter");
ok(await n() === N0 + 2 && await story(6).locator("a").getAttribute("href") === "https://www.nytimes.com/2026/10/27/us/another-story.html", "Enter on a summary → paste link → story added below");
ok(await f(6, "outlet").evaluate(e => e.textContent.length > 0), "outlet filled in from the link");

console.log(`[${engine}] arrows`);
await end(f(7, "head")); await p.keyboard.press("ArrowDown");
ok(await active() === "sum:7", "↓ at a headline's last line → summary");
await p.keyboard.press("ArrowUp");
ok(await active() === "head:7", "↑ at a summary's first line → headline");
await end(f(7, "outlet")); await p.keyboard.press("ArrowRight");
ok(await active() === "head:7", "→ at the end of the outlet → headline");
await p.keyboard.press("ArrowLeft");
ok(await active() === "outlet:7", "← at the start of the headline → outlet");

console.log(`[${engine}] links, remove, reorder`);
await f(8, "head").click();
ok(p.url() === url, "clicking a headline edits it, doesn't navigate");
await f(8, "head").click({ modifiers: ["Meta"] });
ok(await p.evaluate(() => window.__opened) === await story(8).locator("a").getAttribute("href"), "⌘-click opens the story");
const h9 = await txt(f(9, "head"));
await story(9).hover(); await story(9).locator(".x").click();
ok(await n() === N0 + 1, "× removes a story");
await p.locator(".toast button").click();
ok(await n() === N0 + 2 && await txt(f(9, "head")) === h9, "Undo puts it back in place");
const h10 = await txt(f(10, "head"));
await story(10).locator(".grip").focus(); await p.keyboard.press("ArrowUp");
ok(await txt(f(9, "head")) === h10, "grip + ↑ moves a story up");

console.log(`[${engine}] reload + copy`);
const before = await p.evaluate(() => clean(sheet).innerHTML);
await p.reload();
ok(await n() === N0 + 2 && await p.evaluate(() => clean(sheet).innerHTML) === before, "every edit survives a reload");
await end(f(0, "outlet")); await p.keyboard.press("Enter"); await p.keyboard.press("Enter");
ok(await active() === "sum:0" && await n() === N0 + 2, "fields still behave after reload");
await p.locator("button[data-copy=briefing]").click();
await p.waitForFunction(() => window.__copied);
const out = await p.evaluate(() => window.__copied);
ok(!/contenteditable|data-f=|data-ph|<span|tabindex|class=/.test(out), "copied email has no editor markup");
ok((out.match(/<p data-entry/g) || []).length === N0 + 2, "copied email has every story");
ok(out.includes("New summary written by hand.") && out.includes("Pasted from Word with breaks") && out.includes("Summary for the added story."), "copied email has the edits");
ok(/<b>[^<]+<\/b><br><a href="[^"]+"><b>[^<]+<\/b><\/a>(\s*<b>\([^)]+\)<\/b>)?<br>[^<]+<\/p>/.test(out), "each story copies as outlet / linked headline / summary");

console.log(`[${engine}] a sheet saved by the old editor`);
await p.evaluate(() => {
  const k = "mb:" + DATA.date;
  const split = clean(sheet).innerHTML.replace(/(<p data-entry[^>]*>)(<b>[^<]*<\/b><br><a [^>]*><b>[^<]*<\/b><\/a>)<br>/, "$1$2</p><p data-entry=\"\" style=\"x\"><br>");
  localStorage.setItem(k, split);
});
await p.reload();
ok(errors.length === 0, "loads without script errors" + (errors.length ? ": " + errors.join("; ") : ""));
ok(await n() === N0 + 3, "the old split fragment shows as its own block (× removes it)");
await p.locator("#briefing [data-entry]").nth(1).hover(); await p.locator("#briefing [data-entry]").nth(1).locator(".x").click();
ok(await n() === N0 + 2, "…and × clears it");
ok(errors.length === 0, "no script errors anywhere" + (errors.length ? ": " + errors.join("; ") : ""));

await p.evaluate(() => localStorage.clear());
await browser.close();
console.log(fails ? `\n${fails} FAILED` : "\nall passed");
process.exit(fails ? 1 : 0);
