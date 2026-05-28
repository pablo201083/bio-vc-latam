const http = require("http");
const fs   = require("fs");
const path = require("path");
const { spawn } = require("child_process");

const root        = __dirname;
const projectRoot = path.join(__dirname, "..");
const PORT        = 4173;
const MODEL_PORT  = 4174;   // persistent model server

// Resolve Python — prefer local venv so sentence-transformers is available
const VENV_PY_WIN = path.join(projectRoot, ".venv", "Scripts", "python.exe");
const VENV_PY_NIX = path.join(projectRoot, ".venv", "bin", "python");
const PYTHON = fs.existsSync(VENV_PY_WIN) ? VENV_PY_WIN
             : fs.existsSync(VENV_PY_NIX) ? VENV_PY_NIX
             : "python";

// ── Auto-start persistent model server ──────────────────────────────────────
// Kept in memory → first query loads model once, all subsequent ~150ms.
let _modelReady = false;

function startModelServer() {
  const py = spawn(
    PYTHON,
    [path.join(projectRoot, "src", "model_server.py")],
    {
      cwd: projectRoot,
      env: { ...process.env, PYTHONIOENCODING: "utf-8" },
      stdio: ["ignore", "pipe", "pipe"],
    }
  );
  py.stdout.on("data", (d) => {
    const msg = d.toString().trim();
    console.log(`[model] ${msg}`);
    if (msg.includes("Listo") || msg.includes("Ready")) {
      _modelReady = true;
    }
  });
  py.stderr.on("data", (d) => {
    // sentence-transformers logs go to stderr — show them but don't fail
    const msg = d.toString().trim();
    if (msg) console.log(`[model] ${msg}`);
  });
  py.on("close", (code) => {
    _modelReady = false;
    console.log(`[model] Server exited (${code}). Restarting in 3s…`);
    setTimeout(startModelServer, 3000);
  });
  py.on("error", (err) => {
    console.error(`[model] Failed to start: ${err.message}`);
  });
}
startModelServer();

// ── Content types ────────────────────────────────────────────────────────────
const contentTypes = {
  ".html": "text/html; charset=utf-8",
  ".js":   "text/javascript; charset=utf-8",
  ".css":  "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg":  "image/svg+xml",
  ".png":  "image/png",
  ".jpg":  "image/jpeg",
  ".jpeg": "image/jpeg",
  ".ico":  "image/x-icon",
};

function send(res, status, body, type = "text/plain; charset=utf-8") {
  res.writeHead(status, { "Content-Type": type });
  res.end(body);
}

// ── CORS helper ──────────────────────────────────────────────────────────────
function setCORS(res) {
  res.setHeader("Access-Control-Allow-Origin",  "http://127.0.0.1:4173");
  res.setHeader("Access-Control-Allow-Methods", "GET,POST,OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");
}

// ── Python subprocess fallback (latent, intro, etc.) ─────────────────────────
function runPipeline(args, res) {
  setCORS(res);
  const py = spawn(PYTHON, ["pipeline.py", ...args, "--json"], {
    cwd: projectRoot,
    env: { ...process.env, PYTHONIOENCODING: "utf-8" },
  });
  let out = "", err = "";
  py.stdout.on("data", (d) => (out += d));
  py.stderr.on("data", (d) => (err += d));
  py.on("close", (code) => {
    if (code !== 0 || !out.trim()) {
      res.writeHead(500, { "Content-Type": "application/json; charset=utf-8" });
      res.end(JSON.stringify({ error: err.trim() || "pipeline error", code }));
    } else {
      res.writeHead(200, { "Content-Type": "application/json; charset=utf-8" });
      res.end(out.trim());
    }
  });
}

// ── Proxy a request body to the model server ─────────────────────────────────
function proxyToModelServer(bodyStr, res) {
  setCORS(res);
  const bodyBuf = Buffer.from(bodyStr, "utf-8");
  const req = http.request(
    {
      hostname: "127.0.0.1",
      port: MODEL_PORT,
      path: "/query",
      method: "POST",
      headers: {
        "Content-Type":   "application/json",
        "Content-Length": bodyBuf.length,
      },
      timeout: 30000,
    },
    (modelRes) => {
      let out = "";
      modelRes.on("data", (d) => (out += d));
      modelRes.on("end", () => {
        try {
          // Model server returns {results:[...], entities:[...], ms:N, query:...}
          // Forward the full enriched payload to the browser.
          // Legacy fallback: if it's a plain array, wrap it.
          const parsed = JSON.parse(out);
          let payload;
          if (Array.isArray(parsed)) {
            payload = { results: parsed, entities: [], ms: 0 };
          } else {
            payload = {
              results:  parsed.results  || [],
              entities: parsed.entities || [],
              ms:       parsed.ms       || 0,
              query:    parsed.query    || "",
            };
          }
          res.writeHead(200, { "Content-Type": "application/json; charset=utf-8" });
          res.end(JSON.stringify(payload));
        } catch {
          res.writeHead(200, { "Content-Type": "application/json; charset=utf-8" });
          res.end(out);
        }
      });
    }
  );
  req.on("error",   () => proxyFallback(bodyStr, res));
  req.on("timeout", () => { req.destroy(); proxyFallback(bodyStr, res); });
  req.write(bodyBuf);
  req.end();
}

function proxyFallback(bodyStr, res) {
  // Model server not ready → fall back to spawning Python
  try {
    const { query, top_k = 20, theme, country, stage } = JSON.parse(bodyStr);
    const args = ["query", ...query.split(" "), "--top-k", String(top_k)];
    if (theme)   args.push("--theme",   theme);
    if (country) args.push("--country", country);
    if (stage)   args.push("--stage",   stage);
    runPipeline(args, res);
  } catch (e) {
    res.writeHead(400); res.end(JSON.stringify({ error: e.message }));
  }
}

// ── Main request handler ──────────────────────────────────────────────────────
http.createServer((req, res) => {

  if (req.method === "OPTIONS") {
    setCORS(res);
    res.writeHead(204);
    res.end();
    return;
  }

  // ── GET /api/model-ready — health check for the browser ──
  if (req.method === "GET" && req.url === "/api/model-ready") {
    setCORS(res);
    // Quick TCP probe to model server
    const probe = http.get(
      { hostname: "127.0.0.1", port: MODEL_PORT, path: "/health", timeout: 1000 },
      (r) => {
        let body = "";
        r.on("data", (d) => (body += d));
        r.on("end", () => {
          try {
            const data = JSON.parse(body);
            const ready = data.status === "ready";
            _modelReady = ready;
            res.writeHead(200, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ ready, vectors: data.vectors || 0 }));
          } catch {
            res.writeHead(200, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ ready: false }));
          }
        });
      }
    );
    probe.on("error", () => {
      _modelReady = false;
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ ready: false }));
    });
    probe.on("timeout", () => {
      probe.destroy();
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ ready: false }));
    });
    return;
  }

  // ── POST /api/query — semantic search (fast path: model server) ──
  if (req.method === "POST" && req.url === "/api/query") {
    let body = "";
    req.on("data", (c) => (body += c));
    req.on("end", () => {
      try {
        const parsed = JSON.parse(body);
        if (!parsed.query) {
          res.writeHead(400);
          res.end(JSON.stringify({ error: "missing query" }));
          return;
        }
        // Build model-server payload (keeps filters)
        const payload = JSON.stringify({
          query:   parsed.query,
          top_k:   parsed.top_k || 20,
          filters: {
            theme:   parsed.theme   || undefined,
            country: parsed.country || undefined,
            stage:   parsed.stage   || undefined,
          },
        });
        proxyToModelServer(payload, res);
      } catch (e) {
        res.writeHead(400);
        res.end(JSON.stringify({ error: e.message }));
      }
    });
    return;
  }

  // ── POST /api/latent ──
  if (req.method === "POST" && req.url === "/api/latent") {
    let body = "";
    req.on("data", (c) => (body += c));
    req.on("end", () => {
      try {
        const { entity_id, top_k = 15 } = JSON.parse(body);
        if (!entity_id) {
          res.writeHead(400);
          res.end(JSON.stringify({ error: "missing entity_id" }));
          return;
        }
        runPipeline(["latent", entity_id, "--top-k", String(top_k)], res);
      } catch (e) {
        res.writeHead(400);
        res.end(JSON.stringify({ error: e.message }));
      }
    });
    return;
  }

  // ── POST /api/intro ──
  if (req.method === "POST" && req.url === "/api/intro") {
    let body = "";
    req.on("data", (c) => (body += c));
    req.on("end", () => {
      try {
        const { entity_a, entity_b, no_cab = false } = JSON.parse(body);
        if (!entity_a || !entity_b) {
          res.writeHead(400);
          res.end(JSON.stringify({ error: "missing entity_a or entity_b" }));
          return;
        }
        const args = ["intro", entity_a, entity_b];
        if (no_cab) args.push("--no-cab");
        runPipeline(args, res);
      } catch (e) {
        res.writeHead(400);
        res.end(JSON.stringify({ error: e.message }));
      }
    });
    return;
  }

  // ── Static files ──────────────────────────────────────────────────────────
  const requested = req.url === "/" ? "/index.html" : req.url.split("?")[0];
  const safePath  = path.normalize(path.join(root, requested));

  if (!safePath.startsWith(root)) {
    send(res, 403, "Forbidden");
    return;
  }

  fs.readFile(safePath, (err, data) => {
    if (err) { send(res, 404, "Not found"); return; }
    const ext = path.extname(safePath).toLowerCase();
    send(res, 200, data, contentTypes[ext] || "application/octet-stream");
  });

}).listen(PORT, "127.0.0.1", () => {
  console.log(`Pilot en http://127.0.0.1:${PORT}`);
  console.log(`Modelo cargando en background (puerto ${MODEL_PORT})…`);
});
