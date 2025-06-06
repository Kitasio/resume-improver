import asyncio
from crawl4ai import AsyncWebCrawler, CrawlResult, CrawlerRunConfig
from crawl4ai.deep_crawling import BestFirstCrawlingStrategy
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy
from crawl4ai.deep_crawling.scorers import KeywordRelevanceScorer

JOB_KEYWORDS = [
    "job",
    "jobs",
    "career",
    "careers",
    "openings",
    "hiring",
    "position",
    "positions",
    "vacancy",
    "vacancies",
    "employment",
    "work",
    "work-with-us",
    "join-us",
    "internship",
    "internships",
    "opportunities",
    "apply",
    "now-recruiting",
]


async def main():
    # Create a scorer
    scorer = KeywordRelevanceScorer(keywords=JOB_KEYWORDS, weight=0.7)

    # Configure the strategy
    strategy = BestFirstCrawlingStrategy(
        max_depth=2,
        include_external=False,
        url_scorer=scorer,
        max_pages=25,  # Maximum number of pages to crawl (optional)
    )

    config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        scraping_strategy=LXMLWebScrapingStrategy(),
        verbose=True,
    )

    async with AsyncWebCrawler() as crawler:
        results: list[CrawlResult] = await crawler.arun(
            "https://landing.jobs/", config=config
        )

        print(f"Crawled {len(results)} pages in total")

        # Access individual results
        for result in results[:10]:  # Show first 10 results
            print(f"URL: {result.url}")
            print(f"Depth: {result.metadata.get('depth', 0)}")


if __name__ == "__main__":
    asyncio.run(main())
