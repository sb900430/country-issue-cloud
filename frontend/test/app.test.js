import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import { JSDOM } from "jsdom";

import { createIssueCloudApp } from "../src/app.js";

function issue(label, labelKo = label) {
  return {
    keyword_id: `keyword-${label.toLowerCase()}`,
    label,
    label_ko: labelKo,
    rank: 1,
    document_frequency: 1,
    publisher_count: 1,
    article_ratio: 1,
    evidence_expressions: [label],
    related_articles: [{
      article_id: `article-${label.toLowerCase()}`,
      title: `${label} article`,
      publisher: "Publisher",
      published_at: "2026-08-06T01:00:00Z",
      url: "https://example.com/article",
    }],
  };
}

function result() {
  const labels = {
    US: ["US issue", "미국 이슈"],
    JP: ["JP issue", "일본 이슈"],
    KR: ["한국 이슈", "한국 이슈"],
  };
  return {
    date: "2026-08-06",
    generated_at: "2026-08-06T01:00:00Z",
    countries: Object.fromEntries(["US", "JP", "KR"].map((country) => [country, {
      status: "success",
      article_count: 120,
      warnings: [],
      top_keywords: [issue(...labels[country])],
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
  assert.equal(dom.window.document.querySelectorAll("[data-date-strip] button").length, 1);
  assert.match(dom.window.document.querySelector("[data-current-date]").textContent, /2026/);
  const languageControl = dom.window.document.querySelector("[data-keyword-language-control]");
  assert.equal(languageControl.hidden, true);

  dom.window.document.querySelector("[data-country='US']").click();
  assert.equal(dom.window.document.querySelector("[data-country='US']").classList.contains("is-active"), true);
  assert.equal(languageControl.hidden, false);
  assert.match(dom.window.document.querySelector("[data-issues]").textContent, /미국 이슈/);
  assert.match(dom.window.document.querySelector("[data-issues]").textContent, /기사 1건/);

  const language = dom.window.document.querySelector("[data-keyword-language]");
  language.checked = false;
  language.dispatchEvent(new dom.window.Event("change"));
  assert.match(dom.window.document.querySelector("[data-issues]").textContent, /US issue/);

  dom.window.document.querySelector("[data-country='JP']").click();
  assert.equal(languageControl.hidden, false);
  assert.match(dom.window.document.querySelector("[data-issues]").textContent, /JP issue/);
  language.checked = true;
  language.dispatchEvent(new dom.window.Event("change"));
  assert.match(dom.window.document.querySelector("[data-issues]").textContent, /일본 이슈/);

  dom.window.document.querySelector("[data-country='KR']").click();
  assert.equal(languageControl.hidden, true);
  dom.window.document.querySelector("[data-country='US']").click();
  assert.equal(languageControl.hidden, false);
  assert.match(dom.window.document.querySelector("[data-issues]").textContent, /미국 이슈/);

  const layout = dom.window.document.querySelector("[data-layout]");
  layout.checked = true;
  layout.dispatchEvent(new dom.window.Event("change"));
  assert.equal(dom.window.document.querySelector("[data-issues]").classList.contains("issues--cloud"), true);

  const dialog = dom.window.document.querySelector("[data-dialog]");
  dialog.showModal = () => dialog.setAttribute("open", "");
  dom.window.document.querySelector(".issue").click();
  assert.equal(dialog.hasAttribute("open"), true);
  assert.match(dom.window.document.querySelector("[data-dialog-title]").textContent, /미국 이슈/);

  language.checked = false;
  language.dispatchEvent(new dom.window.Event("change"));
  assert.match(dom.window.document.querySelector("[data-dialog-title]").textContent, /US issue/);
});

test("date tabs render oldest on the left and newest on the right", async () => {
  const html = readFileSync(new URL("../index.html", import.meta.url), "utf8");
  const dom = new JSDOM(html, { url: "https://example.test/country-issue-cloud/" });
  const days = ["2026-08-06", "2026-08-04", "2026-08-05"].map((date) => ({
    date,
    status: "success",
    countries: {},
  }));
  const app = createIssueCloudApp({
    root: dom.window.document,
    dataSource: {
      usedCache: false,
      getLatest: async () => result(),
      getCalendar: async () => ({ schema_version: "1.0", days }),
      getStatus: async () => ({ schema_version: "1.0", status: "success" }),
      getByDate: async () => result(),
    },
    logger: { error: () => {} },
  });

  assert.equal(await app.start(), true);
  const buttons = [...dom.window.document.querySelectorAll("[data-date-strip] button")];
  assert.deepEqual(
    buttons.map((button) => button.dataset.dateValue),
    ["2026-08-04", "2026-08-05", "2026-08-06"],
  );
  assert.equal(buttons.at(-1).classList.contains("is-active"), true);
});

test("metadata failure does not hide latest data and partial country is explained", async () => {
  const html = readFileSync(new URL("../index.html", import.meta.url), "utf8");
  const dom = new JSDOM(html, { url: "https://example.test/country-issue-cloud/" });
  const partial = result();
  partial.status = "partial_success";
  partial.countries.JP = {
    status: "failed",
    article_count: 41,
    warnings: ["keyword_analysis_failed:ValueError"],
    top_keywords: [],
  };
  const app = createIssueCloudApp({
    root: dom.window.document,
    dataSource: {
      usedCache: false,
      getLatest: async () => partial,
      getDates: async () => { throw new Error("dates unavailable"); },
      getCalendar: async () => { throw new Error("calendar unavailable"); },
      getStatus: async () => { throw new Error("status unavailable"); },
      getByDate: async () => partial,
    },
    logger: { error: () => {} },
  });

  assert.equal(await app.start(), true);
  assert.match(dom.window.document.querySelector("[data-issues]").textContent, /한국 이슈/);
  dom.window.document.querySelector("[data-country='JP']").click();
  assert.match(dom.window.document.querySelector("[data-run-status]").textContent, /41\/50/);
  assert.equal(dom.window.document.querySelector("[data-country='JP']").classList.contains("is-unavailable"), true);
});
