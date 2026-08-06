import assert from "node:assert/strict";
import test from "node:test";

import { createCountryView } from "../src/view-model.js";

test("country view keeps the five independent ranked issues", () => {
  const issues = Array.from({ length: 5 }, (_, index) => ({ rank: index + 1 }));
  const result = {
    date: "2026-08-06",
    generated_at: "2026-08-06T01:00:00Z",
    countries: {
      KR: { status: "success", article_count: 30, warnings: [], top_issues: issues },
    },
  };

  const view = createCountryView(result, "KR");

  assert.equal(view.code, "KR");
  assert.deepEqual(view.issues.map((issue) => issue.rank), [1, 2, 3, 4, 5]);
  assert.ok(view.issues[0].weight > view.issues[4].weight);
});
