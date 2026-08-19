import { CachedIssueDataSource } from "./cached-data-source.js";
import { StaticJsonDataSource } from "./data-source.js";
import { createCountryView } from "./view-model.js";

export function createIssueCloudApp({
  root = document,
  dataSource = new CachedIssueDataSource(new StaticJsonDataSource("./data/v2")),
  logger = console,
} = {}) {
  const state = {
    result: null,
    calendar: [],
    publicationStatus: null,
    usingCache: false,
    country: "KR",
    layout: "tiles",
    bound: false,
  };
  const elements = {
    countries: root.querySelector("[data-countries]"),
    date: root.querySelector("[data-date]"),
    dateStrip: root.querySelector("[data-date-strip]"),
    currentDate: root.querySelector("[data-current-date]"),
    generated: root.querySelector("[data-generated]"),
    articleCount: root.querySelector("[data-article-count]"),
    issues: root.querySelector("[data-issues]"),
    runStatus: root.querySelector("[data-run-status]"),
    status: root.querySelector("[data-status]"),
    retry: root.querySelector("[data-retry]"),
    refresh: root.querySelector("[data-refresh]"),
    layout: root.querySelector("[data-layout]"),
    dialog: root.querySelector("[data-dialog]"),
    dialogTitle: root.querySelector("[data-dialog-title]"),
    dialogArticles: root.querySelector("[data-dialog-articles]"),
  };

  async function start() {
    bindEvents();
    state.calendar = [];
    state.publicationStatus = null;
    setInteractive(false);
    elements.retry.hidden = true;
    announce("데이터를 불러오는 중입니다 · データを読み込み中です");
    try {
      const latest = await dataSource.getLatest();
      state.result = latest;
      state.usingCache = dataSource.usedCache === true;
      render();
      setInteractive(true);

      const [calendarResult, statusResult] = await Promise.allSettled([
        loadCalendar(),
        typeof dataSource.getStatus === "function"
          ? dataSource.getStatus()
          : Promise.reject(new Error("status_unavailable")),
      ]);
      state.calendar = calendarResult.status === "fulfilled"
        ? calendarResult.value.days
        : [calendarDayFromResult(latest)];
      state.publicationStatus = statusResult.status === "fulfilled" ? statusResult.value : null;
      renderDates(state.calendar, latest.date);
      render();
      setInteractive(true);
      announce(state.usingCache ? "저장된 데이터를 표시합니다 · 保存データを表示中" : "");
      return true;
    } catch (error) {
      state.result = null;
      logger.error("Issue data initialization failed", error);
      announce("데이터를 불러오지 못했습니다. 다시 시도해 주세요 · データを読み込めませんでした。再試行してください", true);
      elements.retry.hidden = false;
      return false;
    }
  }

  async function loadCalendar() {
    if (typeof dataSource.getCalendar === "function") {
      try {
        return await dataSource.getCalendar();
      } catch (error) {
        logger.error("Issue calendar loading failed", error);
      }
    }
    const dates = await dataSource.getDates();
    return {
      schema_version: "1.0",
      days: dates.map((date) => date === state.result.date
        ? calendarDayFromResult(state.result)
        : { date, status: "success", countries: {} }),
    };
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
    elements.date.addEventListener("change", () => loadDate(elements.date.value));
    elements.dateStrip.addEventListener("click", (event) => {
      const button = event.target.closest("button[data-date-value]");
      if (!button || !state.result) return;
      elements.date.value = button.dataset.dateValue;
      loadDate(button.dataset.dateValue);
    });
    elements.retry.addEventListener("click", start);
    elements.refresh.addEventListener("click", start);
    root.querySelector("[data-dialog-close]").addEventListener("click", () => {
      elements.dialog.close();
    });
  }

  function setInteractive(enabled) {
    for (const control of elements.countries.querySelectorAll("button")) {
      control.disabled = !enabled;
    }
    elements.date.disabled = !enabled || state.calendar.length === 0;
    for (const control of elements.dateStrip.querySelectorAll("button")) {
      control.disabled = !enabled || state.calendar.length === 0;
    }
    elements.layout.disabled = !enabled;
    elements.refresh.disabled = !enabled;
  }

  function renderDates(days, selected) {
    elements.date.replaceChildren(
      ...days.map((day) => {
        const option = root.createElement("option");
        option.value = day.date;
        option.textContent = `${day.date}${statusSuffix(day.status)}`;
        option.selected = day.date === selected;
        return option;
      }),
    );
    elements.dateStrip.replaceChildren(
      ...days.map((day) => {
        const value = new Date(`${day.date}T00:00:00Z`);
        const button = root.createElement("button");
        button.type = "button";
        button.dataset.dateValue = day.date;
        button.classList.toggle("is-active", day.date === selected);
        button.classList.toggle("is-partial", day.status === "partial_success");
        button.classList.toggle("is-failed", day.status === "failed");
        button.title = day.status === "success"
          ? "게시 완료 · 公開完了"
          : day.status === "partial_success"
            ? "일부 국가만 게시 · 一部の国のみ公開"
            : "게시 기준 미달 · 公開基準未達";
        button.innerHTML = `<strong>${value.getUTCMonth() + 1}.${value.getUTCDate()}</strong><small>${new Intl.DateTimeFormat("ko-KR", { weekday: "short", timeZone: "UTC" }).format(value)}</small>`;
        return button;
      }),
    );
  }

  async function loadDate(date) {
    if (!state.result) return;
    setInteractive(false);
    try {
      state.result = await dataSource.getByDate(date);
      state.usingCache = dataSource.usedCache === true;
      renderDates(state.calendar, date);
      render();
      announce(dataSource.usedCache ? "저장된 데이터를 표시합니다 · 保存データを表示中" : "");
    } catch (error) {
      logger.error("Issue date loading failed", error);
      announce("선택한 날짜를 불러오지 못했습니다 · 選択日を読み込めませんでした", true);
    } finally {
      setInteractive(true);
    }
  }

  function render() {
    if (!state.result) return;
    const view = createCountryView(state.result, state.country);
    for (const button of elements.countries.querySelectorAll("button")) {
      const selected = button.dataset.country === state.country;
      const countryStatus = state.result.countries[button.dataset.country]?.status;
      button.classList.toggle("is-active", selected);
      button.classList.toggle("is-unavailable", countryStatus === "failed");
      button.setAttribute("aria-pressed", String(selected));
      button.title = countryStatus === "failed"
        ? "오늘 게시 기준 미달 · 本日の公開基準未達"
        : "";
    }
    elements.generated.textContent = new Intl.DateTimeFormat("ko-KR", {
      hour: "2-digit",
      minute: "2-digit",
    }).format(new Date(view.generatedAt));
    elements.currentDate.textContent = new Intl.DateTimeFormat("ko-KR", {
      year: "numeric", month: "long", day: "numeric",
    }).format(new Date(`${view.date}T00:00:00Z`));
    elements.articleCount.textContent = view.articleCount;
    elements.issues.className = `issues issues--${state.layout}`;
    elements.issues.replaceChildren(...view.issues.map(issueButton));
    if (view.issues.length === 0) {
      const empty = root.createElement("p");
      empty.className = "empty";
      empty.textContent = "표시할 키워드가 없습니다 · 表示できるキーワードがありません";
      elements.issues.append(empty);
    }
    renderRunStatus(view);
  }

  function renderRunStatus(view) {
    const messages = [];
    const currentStatus = state.publicationStatus;
    if (
      currentStatus &&
      currentStatus.status === "failed" &&
      currentStatus.attempted_date !== state.result.date
    ) {
      messages.push(
        `${currentStatus.attempted_date} 수집 결과는 게시 기준 미달입니다. ` +
        `${currentStatus.displayed_date} 데이터를 표시합니다`,
      );
    }
    if (view.status === "failed") {
      const reason = view.articleCount < 50
        ? `기사 ${view.articleCount}/50건`
        : "품질을 통과한 키워드 부족";
      messages.push(`${view.local}: ${reason} · 公開基準未達`);
    } else if (state.result.status === "partial_success") {
      messages.push("일부 국가만 게시된 날짜입니다 · 一部の国のみ公開された日です");
    }
    if (state.usingCache) {
      messages.push("네트워크 오류로 저장된 데이터를 표시 중입니다 · 保存データを表示中です");
    }
    elements.runStatus.hidden = messages.length === 0;
    elements.runStatus.textContent = messages.join(" · ");
  }

  function issueButton(issue) {
    const button = root.createElement("button");
    button.className = "issue";
    button.style.setProperty("--weight", issue.weight);
    button.innerHTML = `<span class="issue__rank">${issue.rank}</span><strong></strong><span class="issue__meta"></span>`;
    button.querySelector("strong").textContent = issue.display_label_ko;
    button.querySelector(".issue__meta").textContent = `기사 ${issue.article_count}건 · 매체 ${issue.publisher_count}곳`;
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

  function statusSuffix(status) {
    if (status === "partial_success") return " (부분 · 一部)";
    if (status === "failed") return " (실패 · 失敗)";
    return "";
  }

  function calendarDayFromResult(result) {
    return {
      date: result.date,
      status: result.status ?? "success",
      countries: Object.fromEntries(
        Object.entries(result.countries).map(([country, value]) => [country, {
          status: value.status,
          article_count: value.article_count,
          reason: value.status === "success"
            ? null
            : value.article_count < 50 ? "insufficient_articles" : "insufficient_keywords",
        }]),
      ),
    };
  }

  return { start };
}

if (typeof document !== "undefined") {
  createIssueCloudApp().start();
}
