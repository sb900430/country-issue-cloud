import assert from "node:assert/strict";
import test from "node:test";

import { CachedIssueDataSource } from "../src/cached-data-source.js";

class MemoryStorage {
  constructor() { this.values = new Map(); }
  getItem(key) { return this.values.get(key) ?? null; }
  setItem(key, value) { this.values.set(key, value); }
  removeItem(key) { this.values.delete(key); }
}

test("cached data source stores successful responses and restores them on failure", async () => {
  const storage = new MemoryStorage();
  const value = {
    schema_version: "1.0",
    date: "2026-08-06",
    generated_at: "2026-08-06T00:00:00Z",
    status: "failed",
    countries: Object.fromEntries(
      ["US", "JP", "KR"].map((country) => [country, {
        status: "failed", article_count: 0, extraction_success_rate: 0,
        top_issues: [], warnings: [],
      }]),
    ),
  };
  const source = { getLatest: async () => value };
  const cached = new CachedIssueDataSource(source, storage);

  assert.deepEqual(await cached.getLatest(), value);
  source.getLatest = async () => { throw new Error("offline"); };
  assert.deepEqual(await cached.getLatest(), value);
  assert.equal(cached.usedCache, true);
});
