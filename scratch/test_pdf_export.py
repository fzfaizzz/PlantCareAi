import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="chrome", headless=True)
        page = await browser.new_page()
        await page.set_content("<h1>Test PDF Generation</h1><p>Testing Playwright native PDF export.</p>")
        out = Path("scratch/test.pdf")
        await page.pdf(path=str(out), format="A4")
        print("PDF generated successfully! Size:", out.stat().st_size)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
