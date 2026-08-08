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
  constructor(baseUrl = "./data/v2", fetcher = globalThis.fetch.bind(globalThis)) {
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
  constructor(baseUrl = "/api/v2", fetcher = globalThis.fetch.bind(globalThis)) {
    super();
    this.baseUrl = baseUrl.replace(/\/$/, "");
    this.fetcher = fetcher;
  }

  async getLatest() {
    return validateIssueResult(await this.#get(`${this.baseUrl}/keywords/latest`));
  }

  async getDates() {
    return validateDates(await this.#get(`${this.baseUrl}/keywords/dates?within_days=7`));
  }

  async getByDate(date) {
    validateDate(date);
    return validateIssueResult(await this.#get(`${this.baseUrl}/keywords/${date}`));
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
    value.schema_version !== "2.0" ||
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
    Array.isArray(result.warnings) &&
    result.warnings.every((warning) => typeof warning === "string") &&
    Array.isArray(result.top_keywords) &&
    result.top_keywords.length <= 5 &&
    (result.status !== "success" || result.top_keywords.length === 5) &&
    result.top_keywords.every((keyword, index) =>
      isTopKeyword(keyword, index + 1, result.article_count))
  );
}

function isTopKeyword(keyword, expectedRank, countryArticleCount) {
  return (
    keyword &&
    keyword.rank === expectedRank &&
    typeof keyword.keyword_id === "string" &&
    /^[a-z0-9][a-z0-9_-]{2,79}$/.test(keyword.keyword_id) &&
    typeof keyword.label === "string" &&
    keyword.label.length >= 2 &&
    Number.isInteger(keyword.document_frequency) &&
    keyword.document_frequency >= 1 &&
    keyword.document_frequency <= countryArticleCount &&
    Number.isInteger(keyword.publisher_count) &&
    keyword.publisher_count >= 1 &&
    typeof keyword.article_ratio === "number" &&
    keyword.article_ratio > 0 &&
    keyword.article_ratio <= 1 &&
    Array.isArray(keyword.evidence_expressions) &&
    keyword.evidence_expressions.length > 0 &&
    Array.isArray(keyword.related_articles) &&
    keyword.related_articles.length > 0 &&
    keyword.related_articles.length <= 20 &&
    keyword.related_articles.every(isRepresentativeArticle)
  );
}

function isRepresentativeArticle(article) {
  return (
    article &&
    typeof article.article_id === "string" &&
    article.article_id.length > 0 &&
    typeof article.title === "string" &&
    article.title.length > 0 &&
    typeof article.publisher === "string" &&
    article.publisher.length > 0 &&
    isTimestamp(article.published_at) &&
    typeof article.url === "string" &&
    article.url.startsWith("https://")
  );
}
