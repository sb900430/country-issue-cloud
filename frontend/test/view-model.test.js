import assert from "node:assert/strict";
import test from "node:test";

import { createCountryView } from "../src/view-model.js";

test("country view keeps the five independent ranked issues", () => {
  const issues = Array.from({ length: 5 }, (_, index) => ({
    rank: index + 1,
    label: `issue ${index + 1}`,
    label_ko: `이슈 ${index + 1}`,
  }));
  const result = {
    date: "2026-08-06",
    generated_at: "2026-08-06T01:00:00Z",
    countries: {
      KR: { status: "success", article_count: 120, warnings: [], top_keywords: issues },
    },
  };

  const view = createCountryView(result, "KR");

  assert.equal(view.code, "KR");
  assert.deepEqual(view.issues.map((issue) => issue.rank), [1, 2, 3, 4, 5]);
  assert.ok(view.issues[0].weight > view.issues[4].weight);
  assert.equal(view.issues[0].display_label_original, "issue 1");
  assert.equal(view.issues[0].display_label_ko, "이슈 1");
  assert.equal(view.issues[0].translation_available, true);
});

test("country view falls back to the original label for legacy data", () => {
  const result = {
    date: "2026-08-06",
    generated_at: "2026-08-06T01:00:00Z",
    countries: {
      JP: {
        status: "success",
        article_count: 120,
        warnings: [],
        top_keywords: [{ rank: 1, label: "半導体" }],
      },
    },
  };

  const issue = createCountryView(result, "JP").issues[0];

  assert.equal(issue.display_label_ko, "半導体");
  assert.equal(issue.translation_available, false);
});
