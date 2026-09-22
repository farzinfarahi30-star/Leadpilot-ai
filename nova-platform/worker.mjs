
const DEFAULT_STATE = {
  platform: { name: "Nova Platform", version: "0.2.0", mode: "self_hosted_edge", createdAt: "" },
  projects: [],
  providers: [
    { id: "local", name: "Nova Local Runtime", kind: "runtime", status: "ready", external: false },
    { id: "cloudflare", name: "Cloudflare Runtime Adapter", kind: "hosting", status: "active", external: true },
    { id: "github", name: "GitHub Source Adapter", kind: "source", status: "active", external: true }
  ],
  audit: []
};

const json = (data, status = 200) => new Response(JSON.stringify(data), {
  status,
  headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" }
});

async function readJson(request, maxBytes = 128000) {
  const len = Number(request.headers.get("content-length") || 0);
  if (len > maxBytes) throw new Error("request_too_large");
  const text = await request.text();
  if (new TextEncoder().encode(text).byteLength > maxBytes) throw new Error("request_too_large");
  return text ? JSON.parse(text) : {};
}

function makeId(prefix) {
  return prefix + "_" + crypto.randomUUID().replaceAll("-", "").slice(0, 14);
}

function audit(state, action, detail) {
  state.audit.unshift({ id: makeId("audit"), action, detail, createdAt: new Date().toISOString() });
  state.audit = state.audit.slice(0, 500);
}

export class NovaState {
  constructor(state) {
    this.storage = state.storage;
    this.ready = state.blockConcurrencyWhile(async () => {
      this.state = await this.storage.get("state");
      if (!this.state) {
        this.state = JSON.parse(JSON.stringify(DEFAULT_STATE));
        this.state.platform.createdAt = new Date().toISOString();
        await this.storage.put("state", this.state);
      }
    });
  }

  async current() {
    await this.ready;
    return this.state;
  }

  async persist(state) {
    await this.storage.put("state", state);
    this.state = state;
  }

  async fetch(request) {
    try {
      const url = new URL(request.url);
      const parts = url.pathname.split("/").filter(Boolean);
      const resource = parts[1];
      const projectId = parts[2];
      const state = await this.current();

      if (resource === "health" && request.method === "GET") {
        return json({
          ok: true,
          platform: "Nova Platform",
          version: "0.2.0",
          mode: "self_hosted_edge",
          vendor_lock_in: false,
          stateful: true,
          runtime: "cloudflare-workers-durable-objects"
        });
      }

      if (resource === "platform" && request.method === "GET") {
        return json({
          ...state.platform,
          projects: state.projects.length,
          providers: state.providers,
          storage: "Durable Object storage"
        });
      }

      if (resource === "providers" && request.method === "GET") return json(state.providers);
      if (resource === "audit" && request.method === "GET") return json(state.audit.slice(0, 100));

      if (resource === "projects" && !projectId && request.method === "GET") {
        return json(state.projects.map(p => ({
          ...p,
          files: Object.keys(p.files || {}).length,
          deployments: (p.deployments || []).length
        })));
      }

      if (resource === "projects" && !projectId && request.method === "POST") {
        const body = await readJson(request);
        const now = new Date().toISOString();
        const name = String(body.name || "Untitled Project").trim().slice(0, 120);
        const description = String(body.description || "").slice(0, 500);
        const project = {
          id: makeId("proj"), name, description, status: "draft",
          createdAt: now, updatedAt: now,
          files: { "README.md": "# " + name + "\n\nManaged by Nova Platform.\n" },
          deployments: [], logs: []
        };
        state.projects.unshift(project);
        audit(state, "project.create", { projectId: project.id, name });
        await this.persist(state);
        return json(project, 201);
      }

      if (resource === "projects" && projectId) {
        const project = state.projects.find(p => p.id === projectId);
        if (!project) return json({ error: "project_not_found" }, 404);

        if (parts.length === 3 && request.method === "GET") return json(project);

        if (parts[3] === "files" && request.method === "GET") {
          return json(Object.entries(project.files).map(([name, content]) => ({ name, content })));
        }

        if (parts[3] === "files" && request.method === "PUT") {
          const body = await readJson(request);
          const filePath = String(body.path || "");
          if (!filePath || filePath.includes("..") || filePath.startsWith("/")) return json({ error: "invalid_path" }, 400);
          project.files[filePath] = String(body.content ?? "");
          project.updatedAt = new Date().toISOString();
          audit(state, "project.file_write", { projectId, path: filePath });
          await this.persist(state);
          return json({ ok: true, path: filePath });
        }

        if (parts[3] === "deploy" && request.method === "POST") {
          const body = await readJson(request);
          const deployment = {
            id: makeId("dep"),
            version: (project.deployments || []).length + 1,
            target: String(body.target || "local"),
            status: "recorded",
            createdAt: new Date().toISOString(),
            files: Object.keys(project.files).length
          };
          project.deployments.unshift(deployment);
          project.status = "deployed";
          project.logs.unshift({
            time: deployment.createdAt,
            level: "info",
            message: "Deployment " + deployment.version + " recorded for " + deployment.target
          });
          audit(state, "project.deploy", { projectId, target: deployment.target, version: deployment.version });
          await this.persist(state);
          return json(deployment, 201);
        }

        if (parts[3] === "logs" && request.method === "GET") return json(project.logs.slice(0, 100));
        if (parts[3] === "cron" && request.method === "GET") return json(project.cron || []);

        if (parts[3] === "cron" && request.method === "POST") {
          const body = await readJson(request);
          project.cron ??= [];
          const job = {
            id: makeId("cron"),
            name: String(body.name || "job").slice(0, 120),
            schedule: String(body.schedule || "0 * * * *").slice(0, 80),
            route: String(body.route || "/"),
            enabled: body.enabled !== false
          };
          project.cron.push(job);
          audit(state, "cron.create", { projectId, job });
          await this.persist(state);
          return json(job, 201);
        }
      }

      return json({ error: "not_found" }, 404);
    } catch (error) {
      const message = String(error?.message || error);
      return json(
        { error: message === "request_too_large" ? "request_too_large" : "internal_error" },
        message === "request_too_large" ? 413 : 500
      );
    }
  }
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname.startsWith("/api/")) {
      const stub = env.NOVA_STATE.get(env.NOVA_STATE.idFromName("global"));
      return stub.fetch(request);
    }
    return env.ASSETS.fetch(request);
  }
};
