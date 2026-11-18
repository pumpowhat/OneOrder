/** Record the real local app, with demo AI and an isolated DB. No API responses are mocked.
 * Windows: node scripts/round3/record_backup.mjs
 * Needs existing frontend/node_modules, Python requirements, Playwright+Chromium,
 * and an H.264 ffmpeg (FFMPEG_EXE, or Python's optional imageio-ffmpeg package).
 * Set PLAYWRIGHT_MODULES when Playwright is supplied outside this repository.
 * Example isolated recorder dependencies:
 *   npm install --prefix .pytest_cache/recorder playwright
 *   npx --prefix .pytest_cache/recorder playwright install chromium
 *   .venv/Scripts/python.exe -m pip install imageio-ffmpeg
 * Then point PLAYWRIGHT_MODULES at .pytest_cache/recorder/node_modules.
 * This is a DRAFT recording of today's UI, awaiting Nghĩa's Round 3 script review.
 */
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { spawn, spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const runtimeModules = process.env.PLAYWRIGHT_MODULES;
const require = createRequire(import.meta.url);
const { chromium } = require(runtimeModules ? path.join(runtimeModules, 'playwright') : 'playwright');
const runDir = path.join(root, '.pytest_cache', `round3-video-${Date.now()}`);
const evidence = path.join(root, 'docs', 'round3', 'evidence');
fs.mkdirSync(runDir, { recursive: true });
fs.mkdirSync(evidence, { recursive: true });
const python = process.env.PYTHON_EXE || path.join(root, '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python');
const backendPort = process.env.VIDEO_BACKEND_PORT || '8211';
const frontendPort = process.env.VIDEO_FRONTEND_PORT || '5311';
const base = `http://127.0.0.1:${frontendPort}`;
const children = [];
const log = { draft: true, reviewed_by_nghia: false, crm_shown: false,
  created_at: new Date().toISOString(), viewport: { width: 1920, height: 1080 },
  mode: 'AI_MODE=demo; isolated SQLite DB; samples/video-demo',
  events: [], browser_errors: [], external_requests: [] };
let browser;
let context;
let page;

function service(command, args, name, extraEnv) {
  const stream = fs.openSync(path.join(runDir, `${name}.log`), 'a');
  const child = spawn(command, args, { cwd: name === 'frontend' ? path.join(root, 'frontend') : root, windowsHide: true,
    env: { ...process.env, ...extraEnv }, stdio: ['ignore', stream, stream] });
  children.push(child);
  child.on('error', error => console.error(`${name}: ${error.message}`));
}
async function ready(url) {
  for (let i = 0; i < 150; i++) {
    try { if ((await fetch(url)).ok) return; } catch {}
    await new Promise(resolve => setTimeout(resolve, 200));
  }
  throw new Error(`Service not ready: ${url}; see ${runDir}`);
}
let recordingStart;
function event(name) {
  const seconds = Math.round((Date.now() - recordingStart) / 100) / 10;
  log.events.push({ seconds, name }); console.log(`${seconds}s ${name}`);
}
async function hold(ms = 1000) { await page.waitForTimeout(ms); }
async function pace(seconds) {
  const remaining = seconds * 1000 - (Date.now() - recordingStart);
  if (remaining > 0) await hold(remaining);
}
async function shot(name) { await page.screenshot({ path: path.join(evidence, `backup-draft-${name}.png`) }); }
async function orders() {
  await page.getByRole('link', { name: 'Orders', exact: true }).click();
  const inbox = page.locator('details').filter({ hasText: 'Sample inbox' }).first();
  await inbox.waitFor({ state: 'attached' });
  // Current markup nests <summary> inside a card. Chromium exposes its native
  // "Details" disclosure; click that real disclosure when the inbox is closed.
  if ((await inbox.getAttribute('open')) === null) await inbox.click({ position: { x: 8, y: 8 } });
  await page.getByText('Sample inbox', { exact: true }).waitFor();
}
async function importOrder(filename) {
  const row = page.getByRole('listitem').filter({ hasText: filename });
  await row.getByRole('button', { name: 'Import order', exact: true }).click();
  await page.waitForURL(/\/orders\/[^/]+$/);
  await page.getByRole('button', { name: 'Edit draft', exact: true }).waitFor();
  await page.evaluate(() => window.scrollTo(0, 0));
  event(`Imported ${filename}`);
}
async function edit({ customer, phone, quantity }) {
  await page.getByRole('button', { name: 'Edit draft', exact: true }).click();
  if (customer) await page.getByLabel('Customer', { exact: true }).fill(customer);
  if (phone) await page.getByLabel('Customer phone', { exact: true }).fill(phone);
  if (quantity) await page.locator('form input[type="number"]').nth(2).fill(String(quantity));
  await hold(800);
  for (const checkbox of await page.locator('form input[type="checkbox"]').all()) await checkbox.check();
  await page.getByRole('button', { name: 'Save draft', exact: true }).click();
  await page.getByRole('button', { name: 'Edit draft', exact: true }).waitFor();
  event('Saved real draft corrections and human line checks');
}
async function planAndConfirm(site) {
  await page.getByRole('button', { name: 'Approve OCR result', exact: true }).click();
  await page.getByRole('button', { name: 'Make plan', exact: true }).waitFor();
  if (site) await page.getByRole('combobox').selectOption(site);
  await page.getByRole('button', { name: 'Make plan', exact: true }).click();
  await page.getByRole('button', { name: 'Confirm order', exact: true }).waitFor();
  await page.evaluate(() => window.scrollTo(0, 0));
  await hold(1800);
  const crossBorder = page.getByText('Cross-border', { exact: true }).first();
  if (await crossBorder.count()) {
    await crossBorder.scrollIntoViewIfNeeded(); await hold(1800);
    await shot('cross-border-plan'); event('Displayed actual cross-border shipment and vehicle plan');
  }
  const late = page.getByLabel('Confirm even though delivery is predicted after the requested date', { exact: true });
  if (await late.count()) { await late.check(); event('Explicitly accepted late ETA on historical demo sample'); }
  const partial = page.getByLabel(/Confirm the available items/);
  if (await partial.count()) throw new Error('Unexpected shortage: stop instead of silently accepting partial order');
  await page.getByRole('button', { name: 'Confirm order', exact: true }).click();
  await page.locator('#main-content').getByText('Order confirmed', { exact: true }).first().waitFor();
  await page.locator('#main-content').getByText('Order confirmed', { exact: true }).first().scrollIntoViewIfNeeded();
  await hold(1200);
  event('Confirmed order; backend stock reservation succeeded');
}

try {
  const health = `http://127.0.0.1:${backendPort}/api/health`;
  try { await fetch(health); throw new Error(`Port ${backendPort} is in use; choose VIDEO_BACKEND_PORT`); }
  catch (error) { if (error.message.includes('is in use')) throw error; }
  try { await fetch(base); throw new Error(`Port ${frontendPort} is in use; choose VIDEO_FRONTEND_PORT`); }
  catch (error) { if (error.message.includes('is in use')) throw error; }
  service(python, ['-m', 'uvicorn', 'backend.main:app', '--host', '127.0.0.1', '--port', backendPort], 'backend', {
    AI_MODE: 'demo', DATABASE_URL: `sqlite:///${path.join(runDir, 'recording.db').replaceAll('\\', '/')}`,
    INBOX_DIR: path.join(root, 'samples', 'video-demo'),
  });
  await ready(health);
  service(process.execPath, [path.join(root, 'frontend', 'node_modules', 'vite', 'bin', 'vite.js'),
    '--host', '127.0.0.1', '--port', frontendPort, '--strictPort'], 'frontend', {
      BACKEND_URL: `http://127.0.0.1:${backendPort}`,
    });
  await ready(base);
  browser = await chromium.launch({ headless: true });
  context = await browser.newContext({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1,
    reducedMotion: 'reduce', recordVideo: { dir: runDir, size: { width: 1920, height: 1080 } } });
  await context.addInitScript(() => localStorage.setItem('oneorder.locale', 'en'));
  page = await context.newPage();
  page.setDefaultTimeout(15000);
  page.on('pageerror', error => log.browser_errors.push(error.message));
  page.on('request', req => {
    const url = new URL(req.url());
    if (!['127.0.0.1', 'localhost'].includes(url.hostname) && !req.url().startsWith('data:')) log.external_requests.push(req.url());
  });
  recordingStart = Date.now();
  await page.goto(base);
  await page.getByRole('heading', { name: 'Dashboard', exact: true }).waitFor();
  event('Opened real Dashboard in demo mode');
  await pace(4); await orders(); await hold(1500); await shot('inbox'); await pace(9);
  await importOrder('dk-odense-order.txt'); await hold(2000); await planAndConfirm();
  await shot('email-confirmed'); await pace(29);
  await orders(); await importOrder('se-handwritten-1.jpg'); await hold(1300);
  await edit({ phone: '+46 70 555 12 34' }); await planAndConfirm(); await pace(51);
  await orders(); await importOrder('se-goteborg-materiallista.xlsx'); await hold(1000);
  await edit({ customer: 'Bygg Väst AB', quantity: 25 }); await planAndConfirm('SITE-SE-02'); await pace(74);
  await orders(); await importOrder('dk-nordhavn-materialeliste.pdf'); await hold(1200);
  await edit({ customer: 'Lars Byg ApS' }); await planAndConfirm(); await shot('pdf-confirmed'); await pace(98);
  await page.getByRole('link', { name: 'Stock', exact: true }).click();
  await page.getByRole('searchbox').fill('HEA 200');
  await hold(1500);
  const expand = page.locator('tbody button').first();
  if (await expand.count()) await expand.click();
  await hold(1800); await shot('stock'); event('Displayed actual post-confirm stock');
  await page.getByRole('link', { name: 'Dashboard', exact: true }).click();
  await page.getByRole('heading', { name: 'Dashboard', exact: true }).waitFor();
  await hold(1000); await shot('dashboard-four');
  const actual = await (await page.request.get(`${base}/api/orders`)).json();
  log.final_orders = actual.map(order => ({ id: order.id, customer: order.customer, status: order.status }));
  if (actual.length !== 4 || actual.some(order => order.status !== 'confirmed')) throw new Error('Final backend state is not four confirmed orders');
  event('Verified four actual confirmed orders via read-only API');
  await pace(112);
  const videoPath = await page.video().path();
  await context.close(); context = null;
  await browser.close(); browser = null;
  let ffmpeg = process.env.FFMPEG_EXE;
  if (!ffmpeg) {
    const find = spawnSync(python, ['-c', 'import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())'], { encoding: 'utf8', windowsHide: true });
    if (find.status === 0) ffmpeg = find.stdout.trim();
  }
  if (!ffmpeg) throw new Error(`Recording complete at ${videoPath}; set FFMPEG_EXE for MP4 conversion`);
  const output = path.join(evidence, 'oneorder-backup-DRAFT.mp4');
  const converted = spawnSync(ffmpeg, ['-y', '-i', videoPath, '-an', '-c:v', 'libx264', '-preset', 'fast',
    '-crf', '21', '-pix_fmt', 'yuv420p', '-r', '25', '-movflags', '+faststart', output], { encoding: 'utf8', windowsHide: true });
  if (converted.status !== 0) throw new Error(converted.stderr);
  log.output = path.relative(root, output); log.bytes = fs.statSync(output).size;
  console.log(`Saved ${output} (${log.bytes} bytes)`);
} catch (error) {
  log.error = error.stack; console.error(error.stack); process.exitCode = 1;
  if (page && !page.isClosed()) await page.screenshot({ path: path.join(runDir, 'failure.png') }).catch(() => {});
} finally {
  if (context) await context.close().catch(() => {});
  if (browser) await browser.close().catch(() => {});
  for (const child of children) child.kill();
  fs.writeFileSync(path.join(evidence, 'backup-draft-recording.json'), JSON.stringify(log, null, 2) + '\n');
  console.log(`Evidence log: ${path.join(evidence, 'backup-draft-recording.json')}`);
  console.log(`Service logs and raw recording: ${runDir}`);
}
