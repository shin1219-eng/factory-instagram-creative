import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import { chromium } from "playwright";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..");

function walk(dir, results = []) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      walk(full, results);
    } else {
      results.push(full);
    }
  }
  return results;
}

function findLatestPromptPack() {
  const productionRoot = path.join(repoRoot, "04_OUTPUT", "production");
  if (!fs.existsSync(productionRoot)) return null;
  const files = walk(productionRoot).filter((f) =>
    /C2_InteractiveFV_.*_prompt-pack\.md$/.test(path.basename(f))
  );
  if (files.length === 0) return null;
  files.sort((a, b) => fs.statSync(b).mtimeMs - fs.statSync(a).mtimeMs);
  return files[0];
}

function pickBackground(text) {
  const rules = [
    { keys: ["黒", "black"], value: ["#0B0C12", "#141A24"] },
    { keys: ["濃紺", "深い青", "navy", "deep blue"], value: ["#0B0F1A", "#151C2A"] },
    { keys: ["グレー", "gray", "grey"], value: ["#0E1116", "#1A1F2B"] },
  ];
  for (const rule of rules) {
    if (rule.keys.some((k) => text.includes(k))) return rule.value;
  }
  return ["#0B0C12", "#171D2B"];
}

function pickAccents(text) {
  const accents = {
    cyan: "#8BE7FF",
    magenta: "#F3B8FF",
    mint: "#8BFFD6",
  };
  const hasCyan = text.includes("シアン") || text.includes("cyan");
  const hasMagenta = text.includes("マゼンタ") || text.includes("magenta") || text.includes("ピンク") || text.includes("pink");
  const hasMint = text.includes("ミント") || text.includes("mint") || text.includes("ミントグリーン");
  return [
    hasCyan ? accents.cyan : accents.cyan,
    hasMagenta ? accents.magenta : accents.magenta,
    hasMint ? accents.mint : accents.mint,
  ];
}

function detectHero(text) {
  if (text.includes("プリズム") || text.includes("prism")) return "prism";
  if (text.includes("リング") || text.includes("loop") || text.includes("ring")) return "ring";
  if (text.includes("ディスク") || text.includes("disc") || text.includes("円盤")) return "disc";
  return "ring";
}

function buildHtml({ bg1, bg2, a1, a2, a3, hero }) {
  const heroMarkup = {
    ring: `
      <div class="hero ring"></div>
      <div class="hero ring inner"></div>
    `,
    prism: `
      <div class="hero prism"></div>
      <div class="hero prism inner"></div>
    `,
    disc: `
      <div class="hero disc"></div>
    `,
  }[hero];

  return `<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>RenderPolish Preview</title>
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
      background: linear-gradient(160deg, var(--bg1), var(--bg2));
      overflow: hidden;
    }
    .halo {
      position: absolute;
      inset: -10% 0 0 0;
      margin: auto;
      width: 1000px;
      height: 1000px;
      border-radius: 50%;
      background: radial-gradient(circle, rgba(255,255,255,0.35) 0%, rgba(255,255,255,0) 70%);
      filter: blur(12px);
      opacity: 0.35;
      top: 420px;
      left: 40px;
    }
    .shadow {
      position: absolute;
      width: 760px;
      height: 160px;
      left: 160px;
      top: 1460px;
      background: rgba(0,0,0,0.6);
      filter: blur(28px);
      border-radius: 50%;
    }
    .hero {
      position: absolute;
      left: 50%;
      top: 52%;
      transform: translate(-50%, -50%);
    }
    .ring {
      width: 560px;
      height: 860px;
      border-radius: 50%;
      background: conic-gradient(from 120deg, var(--a1), var(--a2), var(--a3), var(--a1));
      -webkit-mask: radial-gradient(closest-side, transparent calc(100% - 46px), #000 calc(100% - 46px));
      mask: radial-gradient(closest-side, transparent calc(100% - 46px), #000 calc(100% - 46px));
      filter: drop-shadow(0 0 30px rgba(170, 200, 255, 0.35));
    }
    .ring.inner {
      width: 420px;
      height: 640px;
      opacity: 0.25;
      -webkit-mask: radial-gradient(closest-side, transparent calc(100% - 20px), #000 calc(100% - 20px));
      mask: radial-gradient(closest-side, transparent calc(100% - 20px), #000 calc(100% - 20px));
    }
    .prism {
      width: 620px;
      height: 820px;
      background: linear-gradient(140deg, var(--a1), var(--a2), var(--a3));
      clip-path: polygon(50% 6%, 92% 42%, 50% 94%, 8% 42%);
      filter: drop-shadow(0 0 24px rgba(180, 210, 255, 0.4));
      opacity: 0.92;
    }
    .prism.inner {
      width: 420px;
      height: 560px;
      opacity: 0.18;
      background: #ffffff;
      clip-path: polygon(50% 10%, 86% 44%, 50% 90%, 14% 44%);
    }
    .disc {
      width: 520px;
      height: 520px;
      border-radius: 50%;
      background: radial-gradient(circle, var(--a2) 0%, rgba(20,20,20,1) 60%, #0b0c12 100%);
      box-shadow: 0 0 40px rgba(160, 190, 255, 0.3);
    }
    .grain {
      position: absolute;
      inset: 0;
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='120'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='1'/%3E%3C/filter%3E%3Crect width='120' height='120' filter='url(%23n)' opacity='0.12'/%3E%3C/svg%3E");
      mix-blend-mode: soft-light;
      opacity: 0.18;
    }
  </style>
</head>
<body>
  <div class="frame">
    <div class="halo"></div>
    <div class="shadow"></div>
    ${heroMarkup}
    <div class="grain"></div>
  </div>
</body>
</html>`;
}

async function main() {
  const inputPath = process.argv[2] || findLatestPromptPack();
  if (!inputPath) {
    console.error("No C2 prompt pack found.");
    process.exit(1);
  }
  const content = fs.readFileSync(inputPath, "utf8");
  const text = content.toLowerCase();

  const [bg1, bg2] = pickBackground(text);
  const [a1, a2, a3] = pickAccents(text);
  const hero = detectHero(text);

  const inboxDir = path.dirname(inputPath);
  const dateDir = path.dirname(inboxDir);
  const demoDir = path.join(dateDir, "demo");
  const previewDir = path.join(dateDir, "preview");
  fs.mkdirSync(demoDir, { recursive: true });
  fs.mkdirSync(previewDir, { recursive: true });

  const html = buildHtml({ bg1, bg2, a1, a2, a3, hero });
  const htmlPath = path.join(demoDir, "index.html");
  fs.writeFileSync(htmlPath, html, "utf8");

  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  await page.goto(`file://${htmlPath}`);
  await page.waitForTimeout(200);
  const previewPath = path.join(previewDir, "preview.png");
  await page.screenshot({ path: previewPath });
  await browser.close();

  console.log(`Preview generated: ${previewPath}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
