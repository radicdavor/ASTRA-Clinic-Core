import { spawn } from "node:child_process";
import { mkdirSync, rmSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const frontendDir = resolve(__dirname, "..");
const rootDir = resolve(frontendDir, "..");
const backendDir = join(rootDir, "backend");
const isWindows = process.platform === "win32";
const python = process.env.PYTHON ?? (isWindows ? join(backendDir, ".localrun-venv", "Scripts", "python.exe") : "python");
const node = process.execPath;
const viteCli = join(frontendDir, "node_modules", "vite", "bin", "vite.js");
const playwrightCli = join(frontendDir, "node_modules", "@playwright", "test", "cli.js");
const dbName = `astra_e2e_${Date.now()}`;
const databaseUrl = process.env.ASTRA_E2E_DATABASE_URL ?? `postgresql+psycopg://astra:astra@127.0.0.1:5432/${dbName}`;
const backendUrl = process.env.ASTRA_E2E_BACKEND_URL ?? "http://127.0.0.1:8011";
const frontendUrl = process.env.ASTRA_E2E_FRONTEND_URL ?? "http://127.0.0.1:5174";
const seedFile = process.env.ASTRA_E2E_SEED_FILE ?? join(frontendDir, ".e2e-tmp", "db-backed-seed.json");
const children = [];

function run(command, args, options = {}) {
  return new Promise((resolveRun, reject) => {
    const child = spawn(command, args, {
      cwd: options.cwd ?? rootDir,
      env: { ...process.env, ...(options.env ?? {}) },
      stdio: options.stdio ?? "inherit",
      shell: options.shell ?? false,
    });
    child.on("exit", (code) => {
      if (code === 0) resolveRun();
      else reject(new Error(`${command} ${args.join(" ")} failed with ${code}`));
    });
  });
}

function start(command, args, options = {}) {
  const child = spawn(command, args, {
    cwd: options.cwd ?? rootDir,
    env: { ...process.env, ...(options.env ?? {}) },
    stdio: ["ignore", "pipe", "pipe"],
    shell: options.shell ?? false,
  });
  child.stdout.on("data", (chunk) => process.stdout.write(`[${options.name}] ${chunk}`));
  child.stderr.on("data", (chunk) => process.stderr.write(`[${options.name}] ${chunk}`));
  children.push(child);
  return child;
}

async function waitFor(url, name) {
  const deadline = Date.now() + 60_000;
  let lastError;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(url);
      if (response.ok) return;
      lastError = new Error(`${name} returned ${response.status}`);
    } catch (error) {
      lastError = error;
    }
    await new Promise((resolveWait) => setTimeout(resolveWait, 500));
  }
  throw lastError ?? new Error(`${name} did not become ready`);
}

async function cleanup() {
  for (const child of children.reverse()) {
    if (!child.killed) child.kill("SIGTERM");
  }
  await new Promise((resolveWait) => setTimeout(resolveWait, 1000));
  for (const child of children) {
    if (!child.killed) child.kill("SIGKILL");
  }
  await run(python, [join(rootDir, "scripts", "manage_e2e_database.py"), "drop", databaseUrl]).catch((error) => {
    console.error(`[cleanup] ${error.message}`);
  });
}

process.on("SIGINT", async () => {
  await cleanup();
  process.exit(130);
});

process.on("SIGTERM", async () => {
  await cleanup();
  process.exit(143);
});

try {
  mkdirSync(dirname(seedFile), { recursive: true });
  await run(python, [join(rootDir, "scripts", "manage_e2e_database.py"), "create", databaseUrl]);
  await run(python, ["-m", "alembic", "upgrade", "head"], {
    cwd: backendDir,
    env: { DATABASE_URL: databaseUrl, PYTHONPATH: backendDir },
  });
  await run(python, [join(rootDir, "scripts", "seed_full_stack_e2e.py")], {
    env: {
      DATABASE_URL: databaseUrl,
      PYTHONPATH: backendDir,
      ASTRA_E2E_SEED_FILE: seedFile,
      JWT_SECRET: "e2e-local-jwt-secret-with-no-production-value",
      DEMO_MODE: "true",
      REAL_DATA_ALLOWED: "false",
      CORS_ORIGINS: frontendUrl,
      CORS_ORIGIN_REGEX: "",
    },
  });
  start(python, ["-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8011"], {
    cwd: backendDir,
    name: "backend",
    env: {
      DATABASE_URL: databaseUrl,
      PYTHONPATH: backendDir,
      JWT_SECRET: "e2e-local-jwt-secret-with-no-production-value",
      DEMO_MODE: "true",
      REAL_DATA_ALLOWED: "false",
      CORS_ORIGINS: frontendUrl,
      CORS_ORIGIN_REGEX: "",
    },
  });
  await waitFor(`${backendUrl}/ready`, "backend");
  start(node, [viteCli, "--host", "127.0.0.1", "--port", "5174"], {
    cwd: frontendDir,
    name: "frontend",
    env: { VITE_API_BASE_URL: backendUrl },
  });
  await waitFor(frontendUrl, "frontend");
  await run(node, [playwrightCli, "test", "-c", "playwright.db.config.ts"], {
    cwd: frontendDir,
    env: {
      ASTRA_E2E_SEED_FILE: seedFile,
      ASTRA_E2E_BACKEND_URL: backendUrl,
      ASTRA_E2E_FRONTEND_URL: frontendUrl,
    },
  });
} finally {
  await cleanup();
  rmSync(seedFile, { force: true });
}
