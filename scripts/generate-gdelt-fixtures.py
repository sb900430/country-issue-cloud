import json
from pathlib import Path

COUNTRIES = {
    "US": {
        "domains": ("wsj.com", "bloomberg.com", "cnbc.com", "marketwatch.com", "reuters.com"),
        "titles": (
            "Semiconductor investment expands",
            "Interest rate outlook changes",
            "Dollar volatility increases",
            "Climate policy affects markets",
            "Housing demand slows",
        ),
    },
    "JP": {
        "domains": ("nikkei.com", "toyokeizai.net", "diamond.jp", "jiji.com", "newswitch.jp"),
        "titles": (
            "半導体投資が拡大",
            "政策金利の見通し変化",
            "円相場の変動性が上昇",
            "気候政策が市場に影響",
            "住宅需要が減速",
        ),
    },
    "KR": {
        "domains": ("hankyung.com", "mk.co.kr", "sedaily.com", "edaily.co.kr", "mt.co.kr"),
        "titles": (
            "반도체 투자 확대",
            "기준금리 전망 변화",
            "원화 변동성 상승",
            "기후 정책 시장 영향",
            "주택 수요 둔화",
        ),
    },
}


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    for country, settings in COUNTRIES.items():
        articles = []
        domains = settings["domains"]
        titles = settings["titles"]
        for index in range(120):
            domain = domains[index % len(domains)]
            title = titles[index % len(titles)]
            articles.append(
                {
                    "url": f"https://{domain}/fixture/{country.lower()}/{index:03d}",
                    "title": f"{title} {index:03d}",
                    "seendate": f"20260806T{index % 24:02d}{index % 60:02d}00Z",
                    "domain": domain,
                    "language": {"US": "English", "JP": "Japanese", "KR": "Korean"}[country],
                    "sourcecountry": {
                        "US": "United States",
                        "JP": "Japan",
                        "KR": "South Korea",
                    }[country],
                }
            )
        output = project_root / "sample-data" / "evaluation" / country / "gdelt.json"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps({"articles": articles}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
