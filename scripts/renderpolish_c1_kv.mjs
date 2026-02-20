import fs from "fs";
import path from "path";
import { execFile } from "child_process";
import { fileURLToPath, pathToFileURL } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..");

function ensurePromptPack(inputPath) {
  if (!inputPath) {
    throw new Error("Missing input path to C1 prompt-pack.md");
  }
  const full = path.resolve(inputPath);
  if (!fs.existsSync(full)) {
    throw new Error(`Prompt pack not found: ${full}`);
  }
  return full;
}

function ensureDemoDir(promptPackPath) {
  const inboxDir = path.dirname(promptPackPath);
  const dateDir = path.dirname(inboxDir);
  const demoDir = path.join(dateDir, "demo");
  fs.mkdirSync(demoDir, { recursive: true });
  return demoDir;
}

function getPreviewPath(demoDir) {
  return path.join(demoDir, "preview.png");
}

function getChromePath() {
  const chromePath =
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
  if (!fs.existsSync(chromePath)) {
    throw new Error(`Google Chrome not found at ${chromePath}`);
  }
  return chromePath;
}

function pickBackground(text) {
  if (text.includes("濃紺") || text.includes("深い青") || text.includes("navy")) {
    return ["#0B0F1A", "#151C2A"];
  }
  if (text.includes("黒") || text.includes("black")) {
    return ["#0B0C12", "#141A24"];
  }
  return ["#0B0C12", "#171D2B"];
}

function pickAccents(text) {
  const cyan = "#8BE7FF";
  const magenta = "#F3B8FF";
  const mint = "#8BFFD6";
  if (text.includes("シアン") || text.includes("cyan")) return [cyan, magenta, mint];
  if (text.includes("マゼンタ") || text.includes("pink") || text.includes("ピンク")) {
    return [magenta, cyan, mint];
  }
  return [cyan, magenta, mint];
}

function buildHtml({ bg1, bg2, a1, a2, a3 }) {
  return `<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>C1 RenderPolish KV</title>
  <style>
    :root {
      --bg1: ${bg1};
      --bg2: ${bg2};
      --a1: ${a1};
      --a2: ${a2};
      --a3: ${a3};
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: #000;
      display: grid;
      place-items: center;
      min-height: 100vh;
    }
    .frame {
      position: relative;
      width: 1080px;
      height: 1920px;
      background: radial-gradient(140% 120% at 50% 30%, rgba(255,255,255,0.08) 0%, rgba(0,0,0,0) 40%),
                  linear-gradient(155deg, var(--bg1), var(--bg2));
      overflow: hidden;
    }
    .grain {
      position: absolute;
      inset: 0;
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='140' height='140'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.75' numOctaves='1'/%3E%3C/filter%3E%3Crect width='140' height='140' filter='url(%23n)' opacity='0.12'/%3E%3C/svg%3E");
      mix-blend-mode: soft-light;
      opacity: 0.18;
    }
    .halo {
      position: absolute;
      width: 980px;
      height: 980px;
      left: 50%;
      top: 360px;
      transform: translateX(-50%);
      background: radial-gradient(circle, rgba(255,255,255,0.28) 0%, rgba(255,255,255,0) 70%);
      filter: blur(12px);
      opacity: 0.35;
    }
    .shadow {
      position: absolute;
      width: 760px;
      height: 160px;
      left: 160px;
      top: 1480px;
      background: rgba(0,0,0,0.6);
      filter: blur(28px);
      border-radius: 50%;
    }
    .ring {
      position: absolute;
      left: 50%;
      top: 52%;
      transform: translate(-50%, -50%);
      width: 560px;
      height: 860px;
      border-radius: 50%;
      background: conic-gradient(from 120deg, var(--a1), var(--a2), var(--a3), var(--a1));
      -webkit-mask: radial-gradient(closest-side, transparent calc(100% - 52px), #000 calc(100% - 52px));
      mask: radial-gradient(closest-side, transparent calc(100% - 52px), #000 calc(100% - 52px));
      filter: drop-shadow(0 0 36px rgba(180, 210, 255, 0.45));
    }
    .prism {
      position: absolute;
      left: 50%;
      top: 52%;
      transform: translate(-50%, -50%);
      width: 620px;
      height: 820px;
      background: linear-gradient(140deg, var(--a1), var(--a2), var(--a3));
      clip-path: polygon(50% 6%, 92% 42%, 50% 94%, 8% 42%);
      opacity: 0.9;
      filter: drop-shadow(0 0 24px rgba(180, 210, 255, 0.4));
    }
    .prism.inner {
      width: 420px;
      height: 560px;
      opacity: 0.16;
      background: #ffffff;
      clip-path: polygon(50% 10%, 86% 44%, 50% 90%, 14% 44%);
    }
  </style>
</head>
<body>
  <div class="frame">
    <div class="halo"></div>
    <div class="shadow"></div>
    <div class="ring"></div>
    <div class="prism"></div>
    <div class="prism inner"></div>
    <div class="grain"></div>
  </div>
</body>
</html>`;
}

function runChromeScreenshot(chromePath, demoPath, previewPath) {
  const fileUrl = pathToFileURL(demoPath).toString();
  const args = [
    "--headless=new",
    "--window-size=1080,1920",
    "--virtual-time-budget=5000",
    `--screenshot=${previewPath}`,
    "--hide-scrollbars",
    "--disable-gpu",
    "--no-sandbox",
    fileUrl,
  ];

  return new Promise((resolve, reject) => {
    execFile(chromePath, args, { timeout: 30000 }, (err, stdout, stderr) => {
      if (err) {
        const detail = [
          "Chrome headless failed.",
          `Command: ${chromePath} ${args.join(" ")}`,
          stdout ? `STDOUT:\n${stdout}` : "",
          stderr ? `STDERR:\n${stderr}` : "",
        ]
          .filter(Boolean)
          .join("\n");
        reject(new Error(detail));
        return;
      }
      resolve();
    });
  });
}

async function main() {
  const promptPath = ensurePromptPack(process.argv[2]);
  const content = fs.readFileSync(promptPath, "utf8").toLowerCase();
  const [bg1, bg2] = pickBackground(content);
  const [a1, a2, a3] = pickAccents(content);

  const demoDir = ensureDemoDir(promptPath);
  const demoPath = path.join(demoDir, "index.html");
  const previewPath = getPreviewPath(demoDir);
  const chromePath = getChromePath();

  const html = buildHtml({ bg1, bg2, a1, a2, a3 });
  fs.writeFileSync(demoPath, html, "utf8");

  await runChromeScreenshot(chromePath, demoPath, previewPath);

  if (!fs.existsSync(previewPath)) {
    throw new Error(`preview.png was not created: ${previewPath}`);
  }
  const stat = fs.statSync(previewPath);
  if (stat.size <= 0) {
    throw new Error(`preview.png is empty: ${previewPath}`);
  }

  console.log(`Preview generated: ${previewPath}`);
}

main().catch((err) => {
  console.error(err.message || err);
  process.exit(1);
});
