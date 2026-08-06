import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import { JSDOM } from "jsdom";

import { createIssueCloudApp } from "../src/app.js";

function issue(label) {
  return {
    issue_id: `issue-${label.toLowerCase()}`,
    issue_label: label,
    display_label_ko: label,
    rank: 1,
    article_count: 1,
    publisher_count: 1,
    article_ratio: 1,
    representative_articles: [{
      title: `${label} article`,
      publisher: "Publisher",
      published_at: "2026-08-06T01:00:00Z",
      url: "https://example.com/article",
    }],
  };
}

function result() {
  return {
    date: "2026-08-06",
    generated_at: "2026-08-06T01:00:00Z",
    countries: Object.fromEntries(["US", "JP", "KR"].map((country) => [country, {
      status: "success",
      article_count: 1,
      warnings: [],
      top_issues: [issue(`${country} issue`)],
    }])),
  };
}

test("failed initialization blocks country clicks and retry restores interaction", async () => {
  const html = readFileSync(new URL("../index.html", import.meta.url), "utf8");
  const dom = new JSDOM(html, { url: "https://example.test/country-issue-cloud/" });
  let fails = true;
  const dataSource = {
    usedCache: false,
    getLatest: async () => {
      if (fails) throw new Error("offline");
      return result();
    },
    getDates: async () => ["2026-08-06"],
    getByDate: async () => result(),
  };
  const errors = [];
  const app = createIssueCloudApp({
    root: dom.window.document,
    dataSource,
    logger: { error: (...values) => errors.push(values) },
  });

  assert.equal(await app.start(), false);
  assert.equal(errors.length, 1);
  assert.equal(dom.window.document.querySelector("[data-country='US']").disabled, true);
  assert.equal(dom.window.document.querySelector("[data-retry]").hidden, false);
  assert.match(dom.window.document.querySelector("[data-status]").textContent, /다시 시도/);
  assert.doesNotThrow(() => dom.window.document.querySelector("[data-country='US']").click());

  fails = false;
  dom.window.document.querySelector("[data-retry]").click();
  await new Promise((resolve) => setTimeout(resolve, 0));

  assert.equal(dom.window.document.querySelector("[data-country='US']").disabled, false);
  assert.equal(dom.window.document.querySelector("[data-retry]").hidden, true);
  dom.window.document.querySelector("[data-country='US']").click();
  assert.equal(dom.window.document.querySelector("[data-country='US']").classList.contains("is-active"), true);
  assert.match(dom.window.document.querySelector("[data-issues]").textContent, /US issue/);

  const layout = dom.window.document.querySelector("[data-layout]");
  layout.checked = true;
  layout.dispatchEvent(new dom.window.Event("change"));
  assert.equal(dom.window.document.querySelector("[data-issues]").classList.contains("issues--cloud"), true);

  const dialog = dom.window.document.querySelector("[data-dialog]");
  dialog.showModal = () => dialog.setAttribute("open", "");
  dom.window.document.querySelector(".issue").click();
  assert.equal(dialog.hasAttribute("open"), true);
  assert.match(dom.window.document.querySelector("[data-dialog-title]").textContent, /US issue/);
});
