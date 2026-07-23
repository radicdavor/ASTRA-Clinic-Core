import { spawn } from "node:child_process";
import { randomUUID } from "node:crypto";
import { mkdirSync, readFileSync, rmSync } from "node:fs";
import { createServer } from "node:net";
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
const runId = randomUUID();
const expectedAppName = `ASTRA Clinic Core E2E ${runId}`;
const dbName = `astra_e2e_${Date.now()}`;
const databaseUrl = process.env.ASTRA_E2E_DATABASE_URL ?? `postgresql+psycopg://astra:astra@127.0.0.1:5432/${dbName}`;
const seedFile = process.env.ASTRA_E2E_SEED_FILE ?? join(frontendDir, ".e2e-tmp", "db-backed-seed.json");
const children = [];
const humanSession = process.argv.includes("--human-session");
const preflightOnly = process.argv.includes("--preflight");

function phase(message) {
  process.stdout.write(`[e2e:${runId.slice(0, 8)}] ${message}\n`);
}

function availablePort(startAt) {
  return new Promise((resolvePort, reject) => {
    const server = createServer();
    server.unref();
    server.on("error", (error) => {
      if (error.code === "EADDRINUSE") resolvePort(availablePort(startAt + 1));
      else reject(error);
    });
    server.listen({ host: "127.0.0.1", port: startAt, exclusive: true }, () => {
      const address = server.address();
      server.close(() => resolvePort(address.port));
    });
  });
}

async function resolveServiceUrl(explicitUrl, preferredPort, name) {
  if (!explicitUrl) return `http://127.0.0.1:${await availablePort(preferredPort)}`;
  const url = new URL(explicitUrl);
  const port = Number(url.port);
  if (!port || url.hostname !== "127.0.0.1") {
    throw new Error(`${name} URL must use an explicit 127.0.0.1 port`);
  }
  const available = await availablePort(port);
  if (available !== port) throw new Error(`${name} port ${port} is already in use`);
  return explicitUrl.replace(/\/$/, "");
}

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
  child.on("exit", (code, signal) => {
    if (!child.expectedStop) {
      process.stderr.write(`[${options.name}] exited unexpectedly (code=${code}, signal=${signal})\n`);
    }
  });
  children.push(child);
  return child;
}

async function waitFor(url, name, child, validate = () => true) {
  const deadline = Date.now() + 60_000;
  let lastError;
  while (Date.now() < deadline) {
    if (child.exitCode !== null) throw new Error(`${name} process exited with ${child.exitCode}`);
    try {
      const response = await fetch(url);
      if (response.ok) {
        const body = await response.json().catch(() => null);
        if (validate(body)) return body;
        lastError = new Error(`${name} identity response did not match this test run`);
      } else {
        lastError = new Error(`${name} returned ${response.status}`);
      }
    } catch (error) {
      lastError = error;
    }
    await new Promise((resolveWait) => setTimeout(resolveWait, 500));
  }
  throw lastError ?? new Error(`${name} did not become ready`);
}

function waitForExit(child, timeoutMs) {
  if (child.exitCode !== null) return Promise.resolve();
  return Promise.race([
    new Promise((resolveExit) => child.once("exit", resolveExit)),
    new Promise((resolveTimeout) => setTimeout(resolveTimeout, timeoutMs)),
  ]);
}

async function cleanup() {
  phase("teardown started");
  for (const child of children.reverse()) {
    child.expectedStop = true;
    if (child.exitCode === null) child.kill("SIGTERM");
  }
  await Promise.all(children.map((child) => waitForExit(child, 2_000)));
  for (const child of children) {
    if (child.exitCode !== null) continue;
    if (isWindows) {
      await run("taskkill", ["/PID", String(child.pid), "/T", "/F"], { stdio: "ignore" }).catch(() => {});
    } else {
      child.kill("SIGKILL");
    }
  }
  await Promise.all(children.map((child) => waitForExit(child, 2_000)));
  await run(python, [join(rootDir, "scripts", "manage_e2e_database.py"), "drop", databaseUrl]).catch((error) => {
    console.error(`[cleanup] ${error.message}`);
  });
  phase("teardown completed");
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
  const backendUrl = await resolveServiceUrl(process.env.ASTRA_E2E_BACKEND_URL, 8093, "backend");
  const frontendUrl = await resolveServiceUrl(process.env.ASTRA_E2E_FRONTEND_URL, 5193, "frontend");
  const backendPort = new URL(backendUrl).port;
  const frontendPort = new URL(frontendUrl).port;
  phase(`isolated stack reserved (backend=${backendPort}, frontend=${frontendPort})`);
  mkdirSync(dirname(seedFile), { recursive: true });
  phase("creating isolated PostgreSQL database");
  await run(python, [join(rootDir, "scripts", "manage_e2e_database.py"), "create", databaseUrl]);
  phase("applying migrations");
  await run(python, ["-m", "alembic", "upgrade", "head"], {
    cwd: backendDir,
    env: { DATABASE_URL: databaseUrl, PYTHONPATH: backendDir },
  });
  phase("seeding synthetic data");
  await run(python, [join(rootDir, "scripts", "seed_full_stack_e2e.py")], {
    env: {
      DATABASE_URL: databaseUrl,
      PYTHONPATH: backendDir,
      ASTRA_E2E_SEED_FILE: seedFile,
      JWT_SECRET: "e2e-local-jwt-secret-with-no-production-value",
      DEMO_MODE: "true",
      REAL_DATA_ALLOWED: "false",
      DEMO_PERSONA_SWITCHER_ENABLED: "true",
      CORS_ORIGINS: frontendUrl,
      CORS_ORIGIN_REGEX: "",
      APP_NAME: expectedAppName,
    },
  });
  phase("starting isolated backend");
  const backend = start(python, ["-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", backendPort], {
    cwd: backendDir,
    name: "backend",
    env: {
      DATABASE_URL: databaseUrl,
      PYTHONPATH: backendDir,
      JWT_SECRET: "e2e-local-jwt-secret-with-no-production-value",
      DEMO_MODE: "true",
      REAL_DATA_ALLOWED: "false",
      DEMO_PERSONA_SWITCHER_ENABLED: "true",
      CORS_ORIGINS: frontendUrl,
      CORS_ORIGIN_REGEX: "",
      APP_NAME: expectedAppName,
    },
  });
  await waitFor(
    `${backendUrl}/health`,
    "backend",
    backend,
    (body) => body?.status === "ok" && body?.service === expectedAppName,
  );
  await waitFor(`${backendUrl}/ready`, "backend readiness", backend, (body) => body?.status === "ready");
  phase("starting isolated frontend");
  const frontend = start(node, [viteCli, "--host", "127.0.0.1", "--port", frontendPort, "--strictPort"], {
    cwd: frontendDir,
    name: "frontend",
    env: { VITE_API_BASE_URL: backendUrl },
  });
  await waitFor(`${backendUrl}/api/public-config`, "backend public config", backend, (body) => (
    body?.app_name === expectedAppName
    && body?.demo_mode === true
    && body?.real_data_allowed === false
  ));
  const frontendDeadline = Date.now() + 60_000;
  while (Date.now() < frontendDeadline) {
    if (frontend.exitCode !== null) throw new Error(`frontend process exited with ${frontend.exitCode}`);
    try {
      const response = await fetch(frontendUrl);
      const html = await response.text();
      if (response.ok && html.includes('<div id="root"></div>')) break;
    } catch {
      // Startup polling records the final phase failure below.
    }
    await new Promise((resolveWait) => setTimeout(resolveWait, 500));
  }
  if (Date.now() >= frontendDeadline) throw new Error("frontend did not become ready");
  phase("server identity and readiness checks passed");
  if (humanSession) {
    const seed = JSON.parse(readFileSync(seedFile, "utf-8"));
    const requiredPersonas = ["admin", "receptionist", "nurse", "physician_1", "physician_2"];
    const missingPersonas = requiredPersonas.filter((persona) => !seed.personas?.[persona]);
    if (missingPersonas.length) {
      throw new Error(`Human usability seed is missing personas: ${missingPersonas.join(", ")}`);
    }
    phase("human usability session is ready (synthetic data only)");
    process.stdout.write(`URL: ${frontendUrl}\n`);
    process.stdout.write(`Controller account: ${seed.personas.admin}\n`);
    process.stdout.write(`Synthetic local password: ${seed.password}\n`);
    process.stdout.write("Use the in-app demo role selector to evaluate all five personas.\n");
    process.stdout.write("Press Ctrl+C to stop the session and remove the isolated database.\n");
    if (!preflightOnly) {
      await new Promise(() => {});
    } else {
      phase("human usability preflight passed");
    }
  } else {
    phase("running DB-backed Playwright suite");
    await run(node, [playwrightCli, "test", "-c", "playwright.db.config.ts"], {
      cwd: frontendDir,
      env: {
        ASTRA_E2E_SEED_FILE: seedFile,
        ASTRA_E2E_BACKEND_URL: backendUrl,
        ASTRA_E2E_FRONTEND_URL: frontendUrl,
        ASTRA_E2E_RUN_ID: runId,
        ASTRA_E2E_EXPECTED_APP_NAME: expectedAppName,
      },
    });
    phase("DB-backed Playwright suite passed");
  }
} finally {
  await cleanup();
  rmSync(seedFile, { force: true });
}
