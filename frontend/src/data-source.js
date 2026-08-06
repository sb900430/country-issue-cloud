const COUNTRIES = ["US", "JP", "KR"];

export class IssueDataSource {
  async getLatest() {
    throw new Error("getLatest must be implemented");
  }

  async getDates() {
    throw new Error("getDates must be implemented");
  }

  async getByDate(_date) {
    throw new Error("getByDate must be implemented");
  }
}

export class StaticJsonDataSource extends IssueDataSource {
  constructor(baseUrl = "./data/v1", fetcher = globalThis.fetch) {
    super();
    this.baseUrl = baseUrl.replace(/\/$/, "");
    this.fetcher = fetcher;
  }

  async getLatest() {
    return validateIssueResult(await this.#get(`${this.baseUrl}/latest.json`));
  }

  async getDates() {
    return validateDates(await this.#get(`${this.baseUrl}/dates.json`));
  }

  async getByDate(date) {
    validateDate(date);
    return validateIssueResult(await this.#get(`${this.baseUrl}/${date}.json`));
  }

  async #get(url) {
    const response = await this.fetcher(url, { headers: { Accept: "application/json" } });
    if (!response.ok) {
      throw new DataSourceError("request_failed", response.status);
    }
    return response.json();
  }
}

export class ApiDataSource extends IssueDataSource {
  constructor(baseUrl = "/api/v1", fetcher = globalThis.fetch) {
    super();
    this.baseUrl = baseUrl.replace(/\/$/, "");
    this.fetcher = fetcher;
  }

  async getLatest() {
    return validateIssueResult(await this.#get(`${this.baseUrl}/issues/latest`));
  }

  async getDates() {
    return validateDates(await this.#get(`${this.baseUrl}/issues/dates?within_days=7`));
  }

  async getByDate(date) {
    validateDate(date);
    return validateIssueResult(await this.#get(`${this.baseUrl}/issues/${date}`));
  }

  async #get(url) {
    const response = await this.fetcher(url, { headers: { Accept: "application/json" } });
    if (!response.ok) {
      throw new DataSourceError("request_failed", response.status);
    }
    return response.json();
  }
}

export class DataSourceError extends Error {
  constructor(code, status = 0) {
    super(code);
    this.name = "DataSourceError";
    this.code = code;
    this.status = status;
  }
}

export function validateIssueResult(value) {
  if (
    !value ||
    value.schema_version !== "1.0" ||
    !isDate(value.date) ||
    !isTimestamp(value.generated_at) ||
    !isStatus(value.status)
  ) {
    throw new DataSourceError("invalid_schema");
  }
  if (!value.countries || Object.keys(value.countries).length !== COUNTRIES.length) {
    throw new DataSourceError("invalid_schema");
  }
  for (const country of COUNTRIES) {
    const result = value.countries[country];
    if (!isCountryResult(result)) {
      throw new DataSourceError("invalid_schema");
    }
  }
  return value;
}

export function validateDates(value) {
  if (!Array.isArray(value) || value.some((date) => !isDate(date))) {
    throw new DataSourceError("invalid_schema");
  }
  return value;
}

function validateDate(value) {
  if (!isDate(value)) {
    throw new DataSourceError("invalid_date");
  }
}

function isDate(value) {
  return typeof value === "string" && /^\d{4}-\d{2}-\d{2}$/.test(value);
}

function isTimestamp(value) {
  return typeof value === "string" && !Number.isNaN(Date.parse(value));
}

function isStatus(value) {
  return ["success", "partial_success", "failed"].includes(value);
}

function isCountryResult(result) {
  return (
    result &&
    isStatus(result.status) &&
    Number.isInteger(result.article_count) &&
    result.article_count >= 0 &&
    typeof result.extraction_success_rate === "number" &&
    result.extraction_success_rate >= 0 &&
    result.extraction_success_rate <= 1 &&
    Array.isArray(result.warnings) &&
    result.warnings.every((warning) => typeof warning === "string") &&
    Array.isArray(result.top_issues) &&
    result.top_issues.length <= 5 &&
    result.top_issues.every((issue, index) => isTopIssue(issue, index + 1, result.article_count))
  );
}

function isTopIssue(issue, expectedRank, countryArticleCount) {
  return (
    issue &&
    issue.rank === expectedRank &&
    typeof issue.issue_id === "string" &&
    /^[a-z0-9][a-z0-9_-]{2,99}$/.test(issue.issue_id) &&
    typeof issue.issue_label === "string" &&
    issue.issue_label.length > 0 &&
    typeof issue.display_label_ko === "string" &&
    issue.display_label_ko.length > 0 &&
    Number.isInteger(issue.article_count) &&
    issue.article_count >= 1 &&
    issue.article_count <= countryArticleCount &&
    Number.isInteger(issue.publisher_count) &&
    issue.publisher_count >= 1 &&
    typeof issue.article_ratio === "number" &&
    issue.article_ratio > 0 &&
    issue.article_ratio <= 1 &&
    Array.isArray(issue.representative_articles) &&
    issue.representative_articles.length > 0 &&
    issue.representative_articles.every(isRepresentativeArticle)
  );
}

function isRepresentativeArticle(article) {
  return (
    article &&
    typeof article.title === "string" &&
    article.title.length > 0 &&
    typeof article.publisher === "string" &&
    article.publisher.length > 0 &&
    isTimestamp(article.published_at) &&
    typeof article.url === "string" &&
    article.url.startsWith("https://")
  );
}
