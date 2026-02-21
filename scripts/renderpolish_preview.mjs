import fs from "fs";
import path from "path";
import { execFile } from "child_process";
import { fileURLToPath, pathToFileURL } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..");

function ensureDemoPath(inputPath) {
  if (!inputPath) {
    throw new Error("Missing input path to demo/index.html");
  }
  const full = path.resolve(inputPath);
  if (!fs.existsSync(full)) {
    throw new Error(`demo/index.html not found: ${full}`);
  }
  return full;
}

function getPreviewPath(demoPath) {
  const demoDir = path.dirname(demoPath);
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
  const demoPath = ensureDemoPath(process.argv[2]);
  const previewPath = getPreviewPath(demoPath);
  const chromePath = getChromePath();

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
