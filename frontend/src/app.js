import { CachedIssueDataSource } from "./cached-data-source.js";
import { StaticJsonDataSource } from "./data-source.js";
import { createCountryView } from "./view-model.js";

export function createIssueCloudApp({
  root = document,
  dataSource = new CachedIssueDataSource(new StaticJsonDataSource("./data/v1")),
  logger = console,
} = {}) {
  const state = { result: null, country: "KR", layout: "tiles", bound: false };
  const elements = {
    countries: root.querySelector("[data-countries]"),
    date: root.querySelector("[data-date]"),
    generated: root.querySelector("[data-generated]"),
    issues: root.querySelector("[data-issues]"),
    status: root.querySelector("[data-status]"),
    retry: root.querySelector("[data-retry]"),
    layout: root.querySelector("[data-layout]"),
    dialog: root.querySelector("[data-dialog]"),
    dialogTitle: root.querySelector("[data-dialog-title]"),
    dialogArticles: root.querySelector("[data-dialog-articles]"),
  };

  async function start() {
    bindEvents();
    setInteractive(false);
    elements.retry.hidden = true;
    announce("데이터를 불러오는 중입니다 · データを読み込み中です");
    try {
      const [latest, dates] = await Promise.all([dataSource.getLatest(), dataSource.getDates()]);
      state.result = latest;
      renderDates(dates, latest.date);
      render();
      setInteractive(true);
      announce(dataSource.usedCache ? "저장된 데이터를 표시합니다 · 保存データを表示中" : "");
      return true;
    } catch (error) {
      state.result = null;
      logger.error("Issue data initialization failed", error);
      announce("데이터를 불러오지 못했습니다. 다시 시도해 주세요 · データを読み込めませんでした。再試行してください", true);
      elements.retry.hidden = false;
      return false;
    }
  }

  function bindEvents() {
    if (state.bound) return;
    state.bound = true;
    elements.countries.addEventListener("click", (event) => {
      const button = event.target.closest("button[data-country]");
      if (!button || !state.result) return;
      state.country = button.dataset.country;
      render();
    });
    elements.layout.addEventListener("change", () => {
      if (!state.result) return;
      state.layout = elements.layout.checked ? "cloud" : "tiles";
      render();
    });
    elements.date.addEventListener("change", async () => {
      if (!state.result) return;
      setInteractive(false);
      try {
        state.result = await dataSource.getByDate(elements.date.value);
        render();
        announce(dataSource.usedCache ? "저장된 데이터를 표시합니다 · 保存データを表示中" : "");
      } catch (error) {
        logger.error("Issue date loading failed", error);
        announce("선택한 날짜를 불러오지 못했습니다 · 選択日を読み込めませんでした", true);
      } finally {
        setInteractive(true);
      }
    });
    elements.retry.addEventListener("click", start);
    root.querySelector("[data-dialog-close]").addEventListener("click", () => {
      elements.dialog.close();
    });
  }

  function setInteractive(enabled) {
    for (const control of elements.countries.querySelectorAll("button")) {
      control.disabled = !enabled;
    }
    elements.date.disabled = !enabled;
    elements.layout.disabled = !enabled;
  }

  function renderDates(dates, selected) {
    elements.date.replaceChildren(
      ...dates.map((date) => {
        const option = root.createElement("option");
        option.value = date;
        option.textContent = date;
        option.selected = date === selected;
        return option;
      }),
    );
  }

  function render() {
    if (!state.result) return;
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
      const empty = root.createElement("p");
      empty.className = "empty";
      empty.textContent = "표시할 이슈가 없습니다 · 表示できるイシューがありません";
      elements.issues.append(empty);
    }
  }

  function issueButton(issue) {
    const button = root.createElement("button");
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
        const item = root.createElement("li");
        const link = root.createElement("a");
        link.href = article.url;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        link.textContent = article.title;
        const meta = root.createElement("span");
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

  return { start };
}

if (typeof document !== "undefined") {
  createIssueCloudApp().start();
}
