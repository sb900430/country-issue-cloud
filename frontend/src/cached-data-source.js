import {
  DataSourceError,
  IssueDataSource,
  validateDates,
  validateIssueResult,
} from "./data-source.js";

export class CachedIssueDataSource extends IssueDataSource {
  constructor(source, storage = globalThis.localStorage) {
    super();
    this.source = source;
    this.storage = storage;
    this.usedCache = false;
  }

  async getLatest() {
    return this.#load("latest", () => this.source.getLatest(), validateIssueResult);
  }

  async getDates() {
    return this.#load("dates", () => this.source.getDates(), validateDates);
  }

  async getByDate(date) {
    return this.#load(`date:${date}`, () => this.source.getByDate(date), validateIssueResult);
  }

  async #load(key, request, validate) {
    try {
      const value = await request();
      try {
        this.storage?.setItem(`country-issue-cloud:${key}`, JSON.stringify(value));
      } catch {
        // ブラウザー保存容量が不足しても取得済みdataは表示する。
      }
      this.usedCache = false;
      return value;
    } catch (error) {
      const cached = this.storage?.getItem(`country-issue-cloud:${key}`);
      if (cached) {
        try {
          this.usedCache = true;
          return validate(JSON.parse(cached));
        } catch {
          this.storage?.removeItem(`country-issue-cloud:${key}`);
        }
      }
      throw error instanceof Error ? error : new DataSourceError("request_failed");
    }
  }
}
