import assert from "node:assert/strict";
import test from "node:test";

import {
  ApiDataSource,
  DataSourceError,
  StaticJsonDataSource,
} from "../src/data-source.js";

function issueResult() {
  const country = {
    status: "partial_success",
    article_count: 120,
    top_keywords: [],
    warnings: [],
  };
  return {
    schema_version: "2.0",
    date: "2026-08-06",
    generated_at: "2026-08-06T00:00:00Z",
    status: "partial_success",
    countries: { US: country, JP: country, KR: country },
  };
}

function fetcher(payload, requested) {
  return async (url) => {
    requested.push(url);
    return { ok: true, status: 200, json: async () => payload };
  };
}

test("static and API adapters return the same issue schema", async () => {
  const requested = [];
  const payload = issueResult();
  const staticSource = new StaticJsonDataSource("/data/v2", fetcher(payload, requested));
  const apiSource = new ApiDataSource("/api/v2", fetcher(payload, requested));

  assert.deepEqual(await staticSource.getByDate("2026-08-06"), payload);
  assert.deepEqual(await apiSource.getByDate("2026-08-06"), payload);
  assert.deepEqual(requested, [
    "/data/v2/2026-08-06.json",
    "/api/v2/keywords/2026-08-06",
  ]);
});

test("default fetch keeps the browser global invocation context", async () => {
  const originalFetch = globalThis.fetch;
  const payload = issueResult();
  globalThis.fetch = async function () {
    assert.equal(this, globalThis);
    return { ok: true, status: 200, json: async () => payload };
  };
  try {
    const staticSource = new StaticJsonDataSource("/data/v2");
    const apiSource = new ApiDataSource("/api/v2");
    assert.deepEqual(await staticSource.getLatest(), payload);
    assert.deepEqual(await apiSource.getLatest(), payload);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("data source rejects an incomplete country schema", async () => {
  const payload = issueResult();
  delete payload.countries.KR;
  const source = new StaticJsonDataSource("/data/v2", fetcher(payload, []));

  await assert.rejects(source.getLatest(), (error) => {
    assert.equal(error.code, "invalid_schema");
    return true;
  });
});

test("data source rejects a successful country without five keywords", async () => {
  const payload = issueResult();
  payload.status = "success";
  payload.countries.US = { ...payload.countries.US, status: "success" };
  const source = new StaticJsonDataSource("/data/v2", fetcher(payload, []));

  await assert.rejects(source.getLatest(), (error) => error.code === "invalid_schema");
});

test("data source maps non-success responses without exposing a body", async () => {
  const source = new ApiDataSource("/api/v2", async () => ({ ok: false, status: 503 }));

  await assert.rejects(source.getLatest(), (error) => {
    assert.ok(error instanceof DataSourceError);
    assert.equal(error.status, 503);
    return true;
  });
});

test("data source rejects malformed top issue fields", async () => {
  const payload = issueResult();
  payload.countries.US.top_keywords = [
    {
      rank: 1,
      keyword_id: "us-rate-decision",
      label: "Rate decision",
      document_frequency: 121,
      publisher_count: 2,
      article_ratio: 1.1,
      evidence_expressions: ["rate decision"],
      related_articles: [],
    },
  ];
  const source = new StaticJsonDataSource("/data/v2", fetcher(payload, []));

  await assert.rejects(source.getLatest(), (error) => error.code === "invalid_schema");
});
