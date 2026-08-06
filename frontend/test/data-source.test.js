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
    article_count: 15,
    extraction_success_rate: 1,
    top_issues: [],
    warnings: [],
  };
  return {
    schema_version: "1.0",
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
  const staticSource = new StaticJsonDataSource("/data/v1", fetcher(payload, requested));
  const apiSource = new ApiDataSource("/api/v1", fetcher(payload, requested));

  assert.deepEqual(await staticSource.getByDate("2026-08-06"), payload);
  assert.deepEqual(await apiSource.getByDate("2026-08-06"), payload);
  assert.deepEqual(requested, [
    "/data/v1/2026-08-06.json",
    "/api/v1/issues/2026-08-06",
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
    const staticSource = new StaticJsonDataSource("/data/v1");
    const apiSource = new ApiDataSource("/api/v1");
    assert.deepEqual(await staticSource.getLatest(), payload);
    assert.deepEqual(await apiSource.getLatest(), payload);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("data source rejects an incomplete country schema", async () => {
  const payload = issueResult();
  delete payload.countries.KR;
  const source = new StaticJsonDataSource("/data/v1", fetcher(payload, []));

  await assert.rejects(source.getLatest(), (error) => {
    assert.equal(error.code, "invalid_schema");
    return true;
  });
});

test("data source maps non-success responses without exposing a body", async () => {
  const source = new ApiDataSource("/api/v1", async () => ({ ok: false, status: 503 }));

  await assert.rejects(source.getLatest(), (error) => {
    assert.ok(error instanceof DataSourceError);
    assert.equal(error.status, 503);
    return true;
  });
});

test("data source rejects malformed top issue fields", async () => {
  const payload = issueResult();
  payload.countries.US.top_issues = [
    {
      rank: 1,
      issue_id: "us-rate-decision",
      issue_label: "Rate decision",
      display_label_ko: "금리 결정",
      article_count: 16,
      publisher_count: 2,
      article_ratio: 1.1,
      representative_articles: [],
    },
  ];
  const source = new StaticJsonDataSource("/data/v1", fetcher(payload, []));

  await assert.rejects(source.getLatest(), (error) => error.code === "invalid_schema");
});
