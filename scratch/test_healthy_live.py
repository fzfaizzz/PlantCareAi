import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

BASE_DIR = Path(__file__).resolve().parents[1]
FINAL_ARTIFACTS = Path(r"C:\Users\akhta\.gemini\antigravity\brain\7a2f00bd-7831-4ce1-b3ac-8467320dd957")

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="chrome", headless=True)
        page = await browser.new_page(viewport={"width": 1280, "height": 900})
        await page.goto("http://localhost:8501/?page=Detect", wait_until="domcontentloaded", timeout=20000)
        await page.wait_for_timeout(3000)
        
        healthy_img = BASE_DIR / "dataset" / "test" / "Tomato___healthy" / "test_leaf_001.jpg"
        print(f"Uploading healthy: {healthy_img.name}...", flush=True)
        
        file_input = page.locator('input[type="file"]')
        await file_input.set_input_files(str(healthy_img))
        await page.wait_for_timeout(2000)
        
        run_btn = page.locator('button:has-text("Detect Disease")')
        if await run_btn.count() > 0:
            await run_btn.first.click()
            print("Clicked Detect Disease, waiting for full result...", flush=True)
            # Wait for cards to appear
            await page.locator('.result-info-card').first.wait_for(timeout=30000)
            await page.wait_for_timeout(2000)
            
            shot_path = FINAL_ARTIFACTS / "final-healthy-verified-result.png"
            await page.screenshot(path=str(shot_path), full_page=True)
            print(f"Healthy screenshot saved to {shot_path}", flush=True)
            
            content = await page.content()
            print(f"Healthy Foliage in page: {'Healthy Foliage' in content}", flush=True)
            print(f"Symptoms & Observations in page: {'Symptoms & Observations' in content}", flush=True)
            print(f"Routine Care in page: {'Routine Care' in content}", flush=True)
            print(f"Prevention in page: {'Prevention' in content}", flush=True)
            print(f"Gemini mentioned: {'gemini' in content.lower()}", flush=True)
            print(f"Google mentioned: {'google' in content.lower()}", flush=True)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
