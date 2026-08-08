const COUNTRY_LABELS = {
  US: { code: "US", name: "United States", local: "미국 · アメリカ" },
  JP: { code: "JP", name: "Japan", local: "일본 · 日本" },
  KR: { code: "KR", name: "Korea", local: "한국 · 韓国" },
};

export function createCountryView(result, country) {
  const countryResult = result.countries[country];
  if (!countryResult || !COUNTRY_LABELS[country]) {
    throw new Error("unknown_country");
  }
  return {
    ...COUNTRY_LABELS[country],
    date: result.date,
    generatedAt: result.generated_at,
    status: countryResult.status,
    articleCount: countryResult.article_count,
    warnings: countryResult.warnings,
    issues: countryResult.top_keywords.map((keyword) => ({
      ...keyword,
      display_label_ko: keyword.label,
      article_count: keyword.document_frequency,
      representative_articles: keyword.related_articles,
      weight: Math.max(0.45, 1 - (keyword.rank - 1) * 0.12),
    })),
  };
}
