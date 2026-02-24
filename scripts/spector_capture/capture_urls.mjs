import fs from "fs";
import path from "path";
import https from "https";
import { fileURLToPath } from "url";
import { chromium } from "playwright";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, "..", "..");

const URLS_PATH = process.env.URLS_PATH || path.join(__dirname, "urls.txt");
const OUTPUT_ROOT = process.env.OUTPUT_ROOT || path.join(repoRoot, "05_LOGS", "captures", new Date().toISOString().slice(0, 10));
const LOCAL_SPECTOR = path.join(__dirname, "node_modules", "spectorjs", "dist", "spector.bundle.js");
const SPECTOR_PATH = process.env.SPECTOR_PATH || LOCAL_SPECTOR;
const SPECTOR_URL = process.env.SPECTOR_BUNDLE_URL || "https://cdn.jsdelivr.net/npm/spectorjs@0.9.30/dist/spector.bundle.js";

const HEADLESS = process.env.HEADLESS === "1";
const BYPASS_CSP = process.env.BYPASS_CSP !== "0";
const DISABLE_WEB_SECURITY = process.env.DISABLE_WEB_SECURITY === "1";
const WAIT_MS = Number(process.env.WAIT_MS || 7000);
const WAIT_CANVAS_MS = Number(process.env.WAIT_CANVAS_MS || 15000);
const CAPTURE_TIMEOUT_MS = Number(process.env.CAPTURE_TIMEOUT_MS || 20000);
const CAPTURE_COMMANDS = Number(process.env.CAPTURE_COMMANDS || 400);
const QUICK_CAPTURE = process.env.QUICK_CAPTURE === "1";
const FULL_CAPTURE = process.env.FULL_CAPTURE === "1";
const VIEWPORT = (process.env.VIEWPORT || "1080x1920").split("x").map(Number);
const MAX_URLS = process.env.MAX_URLS ? Number(process.env.MAX_URLS) : null;
const CHANNEL = process.env.CHANNEL || ""; // e.g. chrome

function readUrls(filePath) {
  if (!fs.existsSync(filePath)) {
    throw new Error(`urls file not found: ${filePath}`);
  }
  const lines = fs.readFileSync(filePath, "utf-8").split(/\r?\n/);
  return lines
    .map((l) => l.trim())
    .filter((l) => l && !l.startsWith("#"));
}

function slugify(url) {
  return url
    .replace(/^https?:\/\//, "")
    .replace(/[^a-zA-Z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "")
    .slice(0, 120);
}

function ensureDir(p) {
  fs.mkdirSync(p, { recursive: true });
}

function downloadFile(url, dest) {
  return new Promise((resolve, reject) => {
    ensureDir(path.dirname(dest));
    const file = fs.createWriteStream(dest);
    https
      .get(url, (res) => {
        if (res.statusCode && res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
          downloadFile(res.headers.location, dest).then(resolve).catch(reject);
          return;
        }
        if (res.statusCode !== 200) {
          reject(new Error(`Failed to download ${url}: status ${res.statusCode}`));
          return;
        }
        res.pipe(file);
        file.on("finish", () => file.close(resolve));
      })
      .on("error", (err) => {
        fs.unlink(dest, () => reject(err));
      });
  });
}

async function ensureSpectorBundle() {
  if (fs.existsSync(SPECTOR_PATH)) return SPECTOR_PATH;
  console.log(`Downloading Spector.js bundle: ${SPECTOR_URL}`);
  await downloadFile(SPECTOR_URL, SPECTOR_PATH);
  return SPECTOR_PATH;
}

async function captureInFrame(frame, timeoutMs, waitCanvasMs, spectorSource, captureCommands, quickCapture, fullCapture) {
  return frame.evaluate(async (timeoutMs, waitCanvasMs, spectorSource, captureCommands, quickCapture, fullCapture) => {
    const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
    let canvases = Array.from(document.querySelectorAll("canvas")).filter((c) => c.width && c.height);
    if (!canvases.length) {
      const maxLoops = Math.ceil(waitCanvasMs / 300);
      for (let i = 0; i < maxLoops; i++) {
        await sleep(300);
        canvases = Array.from(document.querySelectorAll("canvas")).filter((c) => c.width && c.height);
        if (canvases.length) break;
      }
    }
    if (!canvases.length) {
      return { ok: false, error: "no-canvas" };
    }
    const canvas = canvases.sort((a, b) => b.width * b.height - a.width * a.height)[0];
    const gl = canvas.getContext("webgl2") || canvas.getContext("webgl");
    let vendor = null;
    let renderer = null;
    if (gl) {
      const debugInfo = gl.getExtension("WEBGL_debug_renderer_info");
      if (debugInfo) {
        vendor = gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL);
        renderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);
      }
    }

    if (!window.SPECTOR && spectorSource) {
      try {
        const script = document.createElement("script");
        script.text = spectorSource;
        (document.head || document.documentElement).appendChild(script);
        await sleep(300);
      } catch (e) {
        // ignore
      }
    }

    if (!window.SPECTOR) {
      return { ok: false, error: "spector-not-loaded", vendor, renderer, canvas: { width: canvas.width, height: canvas.height } };
    }

    const spector = new window.SPECTOR.Spector();
    let captureData = null;

    const setCapture = (cap) => {
      if (!captureData) captureData = cap;
    };

    if (spector.onCapture && spector.onCapture.add) {
      spector.onCapture.add((cap) => setCapture(cap));
    }
    if (spector.onCaptureComplete && spector.onCaptureComplete.add) {
      spector.onCaptureComplete.add((cap) => setCapture(cap));
    }

    if (captureCommands > 0) {
      spector.captureCanvas(canvas, captureCommands, quickCapture, fullCapture);
    } else {
      spector.captureCanvas(canvas);
    }

    const maxLoops = Math.ceil(timeoutMs / 250);
    for (let i = 0; i < maxLoops; i++) {
      if (captureData) break;
      await sleep(250);
    }

    if (!captureData) {
      return { ok: false, error: "capture-timeout", vendor, renderer, canvas: { width: canvas.width, height: canvas.height } };
    }

    const seen = new WeakSet();
    const safe = (value) => {
      try {
        return JSON.stringify(value, (key, val) => {
          if (typeof val === "function") return undefined;
          if (typeof val === "object" && val !== null) {
            if (seen.has(val)) return undefined;
            seen.add(val);
          }
          if (val instanceof ArrayBuffer) return Array.from(new Uint8Array(val));
          return val;
        });
      } catch (e) {
        return null;
      }
    };

    const json = safe(captureData);
    return {
      ok: !!json,
      error: json ? null : "capture-serialize-failed",
      vendor,
      renderer,
      canvas: { width: canvas.width, height: canvas.height },
      capture_json: json,
    };
  }, timeoutMs, waitCanvasMs, spectorSource, captureCommands, quickCapture, fullCapture);
}

async function captureUrl(url) {
  const slug = slugify(url);
  const outDir = path.join(OUTPUT_ROOT, slug);
  const shotsDir = path.join(outDir, "shots");
  const videosDir = path.join(outDir, "videos");
  const spectorDir = path.join(outDir, "spector");
  ensureDir(shotsDir);
  ensureDir(videosDir);
  ensureDir(spectorDir);

  const launchArgs = [
    "--use-gl=desktop",
    "--enable-webgl",
    "--ignore-gpu-blocklist",
    "--disable-features=IsolateOrigins,site-per-process",
  ];
  if (DISABLE_WEB_SECURITY) {
    launchArgs.push("--disable-web-security");
  }

  const browser = await chromium.launch({
    headless: HEADLESS,
    channel: CHANNEL || undefined,
    args: launchArgs,
  });

  const context = await browser.newContext({
    viewport: { width: VIEWPORT[0], height: VIEWPORT[1] },
    recordVideo: { dir: videosDir },
    bypassCSP: BYPASS_CSP,
  });

  const page = await context.newPage();
  const meta = {
    url,
    slug,
    started_at: new Date().toISOString(),
    status: "started",
    bypass_csp: BYPASS_CSP,
    disable_web_security: DISABLE_WEB_SECURITY,
  };

  try {
    const spectorPath = await ensureSpectorBundle();
    const spectorSource = fs.readFileSync(spectorPath, "utf-8");
    await context.addInitScript({ content: spectorSource });

    await page.goto(url, { waitUntil: "domcontentloaded", timeout: 120000 });

    // Let the page settle and render
    await page.waitForTimeout(WAIT_MS);

    // Attempt to wait for any canvas to exist
    try {
      await page.waitForFunction(() => document.querySelectorAll("canvas").length > 0, { timeout: WAIT_CANVAS_MS });
    } catch (e) {
      // continue; some sites still render after interaction
    }

    // Trigger interaction to surface motion / create canvas
    await page.mouse.move(200, 300);
    await page.waitForTimeout(1200);
    await page.mouse.click(VIEWPORT[0] * 0.5, VIEWPORT[1] * 0.5);
    await page.waitForTimeout(600);
    await page.mouse.wheel(0, 800);
    await page.waitForTimeout(600);
    await page.mouse.wheel(0, -800);
    await page.waitForTimeout(600);
    await page.mouse.move(700, 1200);
    await page.waitForTimeout(1200);

    // Inject Spector again post-load (handles CSP edge cases)
    try {
      await page.addScriptTag({ content: spectorSource });
    } catch (e) {
      meta.spector_inject_error = String(e);
    }
    for (const frame of page.frames()) {
      try {
        await frame.addScriptTag({ content: spectorSource });
      } catch (e) {
        // ignore; frame may be cross-origin or blocked
      }
    }

    let captureResult = null;
    let capturedFrameUrl = null;
    for (const frame of page.frames()) {
      try {
        const result = await captureInFrame(frame, CAPTURE_TIMEOUT_MS, WAIT_CANVAS_MS, spectorSource, CAPTURE_COMMANDS, QUICK_CAPTURE, FULL_CAPTURE);
        if (result && result.ok) {
          captureResult = result;
          capturedFrameUrl = frame.url();
          break;
        }
        if (!captureResult) captureResult = result; // keep first failure reason
      } catch (e) {
        // ignore and try next frame
      }
    }

    if (!captureResult) {
      captureResult = { ok: false, error: "capture-no-result" };
    }

    if (!captureResult.ok) {
      meta.status = "capture_failed";
      meta.error = captureResult.error;
    } else {
      meta.status = "captured";
    }

    meta.vendor = captureResult.vendor || null;
    meta.renderer = captureResult.renderer || null;
    meta.canvas = captureResult.canvas || null;
    meta.frame_url = capturedFrameUrl || null;

    if (captureResult.capture_json) {
      fs.writeFileSync(path.join(spectorDir, "capture.json"), captureResult.capture_json);
    }

    try {
      await page.screenshot({ path: path.join(shotsDir, "hero.png"), fullPage: false, timeout: 60000 });
    } catch (e) {
      meta.screenshot_error = String(e);
    }

    await page.waitForTimeout(1200);
  } catch (err) {
    meta.status = "error";
    meta.error = String(err);
  } finally {
    meta.finished_at = new Date().toISOString();
    fs.writeFileSync(path.join(outDir, "meta.json"), JSON.stringify(meta, null, 2));
    await context.close();
    await browser.close();
  }
}

async function main() {
  const urls = readUrls(URLS_PATH);
  const list = MAX_URLS ? urls.slice(0, MAX_URLS) : urls;
  ensureDir(OUTPUT_ROOT);
  console.log(`Output root: ${OUTPUT_ROOT}`);
  console.log(`URLs: ${list.length}`);

  for (const url of list) {
    console.log(`\n[Capture] ${url}`);
    await captureUrl(url);
  }

  console.log("\nDone.");
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
