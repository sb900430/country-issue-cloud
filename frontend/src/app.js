import { CachedIssueDataSource } from "./cached-data-source.js";
import { StaticJsonDataSource } from "./data-source.js";
import { createCountryView } from "./view-model.js";

const source = new CachedIssueDataSource(new StaticJsonDataSource("./data/v1"));
const state = { result: null, country: "KR", layout: "tiles" };
const elements = {
  countries: document.querySelector("[data-countries]"),
  date: document.querySelector("[data-date]"),
  generated: document.querySelector("[data-generated]"),
  issues: document.querySelector("[data-issues]"),
  status: document.querySelector("[data-status]"),
  layout: document.querySelector("[data-layout]"),
  dialog: document.querySelector("[data-dialog]"),
  dialogTitle: document.querySelector("[data-dialog-title]"),
  dialogArticles: document.querySelector("[data-dialog-articles]"),
};

async function start() {
  bindEvents();
  try {
    const [latest, dates] = await Promise.all([source.getLatest(), source.getDates()]);
    state.result = latest;
    renderDates(dates, latest.date);
    render();
    announce(source.usedCache ? "저장된 데이터를 표시합니다 · 保存データを表示中" : "");
  } catch {
    announce("데이터를 불러오지 못했습니다 · データを読み込めませんでした", true);
  }
}

function bindEvents() {
  elements.countries.addEventListener("click", async (event) => {
    const button = event.target.closest("button[data-country]");
    if (!button) return;
    state.country = button.dataset.country;
    render();
  });
  elements.layout.addEventListener("change", () => {
    state.layout = elements.layout.checked ? "cloud" : "tiles";
    render();
  });
  elements.date.addEventListener("change", async () => {
    try {
      state.result = await source.getByDate(elements.date.value);
      render();
      announce(source.usedCache ? "저장된 데이터를 표시합니다 · 保存データを表示中" : "");
    } catch {
      announce("선택한 날짜를 불러오지 못했습니다 · 選択日を読み込めませんでした", true);
    }
  });
  document.querySelector("[data-dialog-close]").addEventListener("click", () => {
    elements.dialog.close();
  });
}

function renderDates(dates, selected) {
  elements.date.replaceChildren(
    ...dates.map((date) => {
      const option = document.createElement("option");
      option.value = date;
      option.textContent = date;
      option.selected = date === selected;
      return option;
    }),
  );
}

function render() {
  const view = createCountryView(state.result, state.country);
  for (const button of elements.countries.querySelectorAll("button")) {
    const selected = button.dataset.country === state.country;
    button.classList.toggle("is-active", selected);
    button.setAttribute("aria-pressed", String(selected));
  }
  elements.generated.textContent = new Intl.DateTimeFormat("ko-KR", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(view.generatedAt));
  elements.issues.className = `issues issues--${state.layout}`;
  elements.issues.replaceChildren(...view.issues.map(issueButton));
  if (view.issues.length === 0) {
    const empty = document.createElement("p");
    empty.className = "empty";
    empty.textContent = "표시할 이슈가 없습니다 · 表示できるイシューがありません";
    elements.issues.append(empty);
  }
}

function issueButton(issue) {
  const button = document.createElement("button");
  button.className = "issue";
  button.style.setProperty("--weight", issue.weight);
  button.innerHTML = `<span class="issue__rank">${issue.rank}</span><strong></strong><span class="issue__meta"></span>`;
  button.querySelector("strong").textContent = issue.display_label_ko;
  button.querySelector(".issue__meta").textContent = `${issue.article_count} articles · ${issue.publisher_count} sources`;
  button.addEventListener("click", () => openDetail(issue));
  return button;
}

function openDetail(issue) {
  elements.dialogTitle.textContent = issue.display_label_ko;
  elements.dialogArticles.replaceChildren(
    ...issue.representative_articles.map((article) => {
      const item = document.createElement("li");
      const link = document.createElement("a");
      link.href = article.url;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      link.textContent = article.title;
      const meta = document.createElement("span");
      meta.textContent = `${article.publisher} · ${new Date(article.published_at).toLocaleString()}`;
      item.append(link, meta);
      return item;
    }),
  );
  elements.dialog.showModal();
}

function announce(message, isError = false) {
  elements.status.textContent = message;
  elements.status.classList.toggle("is-error", isError);
}

start();
