import test from "node:test";
import assert from "node:assert/strict";
import worker from "../nova-audit-worker/worker.mjs";

const originalFetch = globalThis.fetch;
const route = "https://audit.test/api/audit";
const audit = async (url) => {
  const response = await worker.fetch(
    new Request(route, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ url })
    }),
    {}
  );
  return { status: response.status, body: await response.json() };
};

test.afterEach(() => { globalThis.fetch = originalFetch; });

test("rejects local names and all IP literals before fetching", async () => {
  let calls = 0;
  globalThis.fetch = async () => { calls++; throw Error("should not fetch"); };
  for (const url of [
    "http://localhost/",
    "http://router.home.arpa/",
    "http://192.168.1.3/",
    "http://198.18.0.1/",
    "http://[2001:4860:4860::8888]/"
  ]) {
    const result = await audit(url);
    assert.equal(result.status, 422, url);
    assert.match(result.body.error, /private_or_local_target_not_allowed|ip_literal_not_allowed/, url);
  }
  assert.equal(calls, 0);
});

test("rejects a redirect to a local address without following it", async () => {
  const urls = [];
  globalThis.fetch = async (url, init) => {
    urls.push(url);
    assert.equal(init.redirect, "manual");
    return new Response(null, { status: 302, headers: { location: "http://127.0.0.1/admin" } });
  };
  const result = await audit("https://safe.example/");
  assert.equal(result.status, 422);
  assert.equal(result.body.error, "private_or_local_target_not_allowed");
  assert.deepEqual(urls, ["https://safe.example/"]);
});

test("allows a redirect between public hostnames", async () => {
  const urls = [];
  globalThis.fetch = async (url, init) => {
    urls.push(url);
    assert.equal(init.redirect, "manual");
    if (urls.length === 1) {
      return new Response(null, { status: 301, headers: { location: "/about" } });
    }
    return new Response("<!doctype html><html lang='en'><head><title>Example public page</title></head><body><h1>Public page</h1></body></html>", {
      status: 200, headers: { "content-type": "text/html" }
    });
  };
  const result = await audit("https://safe.example/");
  assert.equal(result.status, 200);
  assert.equal(result.body.ok, true);
  assert.equal(result.body.http.status, 200);
  assert.deepEqual(urls, ["https://safe.example/", "https://safe.example/about"]);
});

test("stops after five redirects", async () => {
  let calls = 0;
  globalThis.fetch = async () => {
    calls++;
    return new Response(null, { status: 302, headers: { location: "/loop" } });
  };
  const result = await audit("https://safe.example/");
  assert.equal(result.status, 422);
  assert.equal(result.body.error, "too_many_redirects");
  assert.equal(calls, 6);
});

test("rejects an unsafe redirect with embedded credentials", async () => {
  let calls = 0;
  globalThis.fetch = async () => {
    calls++;
    return new Response(null, { status: 302, headers: { location: "https://user:pass@another.example/" } });
  };
  const result = await audit("https://safe.example/");
  assert.equal(result.status, 422);
  assert.equal(result.body.error, "credentials_in_url_not_allowed");
  assert.equal(calls, 1);
});
