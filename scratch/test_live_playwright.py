import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

BASE_DIR = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = Path(r"C:\Users\akhta\.gemini\antigravity\brain\7a2f00bd-7831-4ce1-b3ac-8467320dd957")

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="chrome", headless=True)
        page = await browser.new_page(viewport={"width": 1280, "height": 900})
        print("1. Navigating to http://localhost:8501/?page=Detect", flush=True)
        await page.goto("http://localhost:8501/?page=Detect", wait_until="domcontentloaded", timeout=20000)
        await page.wait_for_timeout(3000)
        
        test_img = BASE_DIR / "dataset" / "test" / "Tomato___Early_blight" / "test_leaf_002.jpg"
        print(f"2. Uploading {test_img.name}...", flush=True)
        
        file_input = page.locator('input[type="file"]')
        await file_input.set_input_files(str(test_img))
        await page.wait_for_timeout(3000)
        
        run_btn = page.locator('button:has-text("Detect Disease")')
        print(f"3. Detect button count: {await run_btn.count()}", flush=True)
        if await run_btn.count() > 0:
            await run_btn.first.click()
            print("4. Clicked Detect Disease, waiting for inference...", flush=True)
            await page.wait_for_timeout(10000)
            
            shot_path = ARTIFACTS_DIR / "final-genuine-model-verified-result.png"
            await page.screenshot(path=str(shot_path), full_page=True)
            print(f"5. Screenshot saved to {shot_path}", flush=True)
            
            content = await page.content()
            print("\n=== VERIFICATION RESULTS ===", flush=True)
            print(f"Tomato: {'Tomato' in content}", flush=True)
            print(f"Early Blight: {'Early Blight' in content}", flush=True)
            print(f"Immediate Treatment / Care: {'Immediate Treatment' in content or 'Immediate Care' in content}", flush=True)
            print(f"Prevention: {'Prevention' in content}", flush=True)
            print(f"Gemini mentioned: {'gemini' in content.lower()}", flush=True)
            print(f"Google mentioned: {'google' in content.lower()}", flush=True)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
