import asyncio
import re
from pathlib import Path
from playwright.async_api import async_playwright

BASE_DIR = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = Path(r"C:\Users\akhta\.gemini\antigravity\brain\7a2f00bd-7831-4ce1-b3ac-8467320dd957")

async def test_ui_detection():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1280, "height": 900})
        
        print("1. Opening http://localhost:8501/?page=Detect ...")
        await page.goto("http://localhost:8501/?page=Detect", wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(2000)
        
        # Test image path
        test_img = BASE_DIR / "dataset" / "test" / "Tomato___Early_blight" / "test_leaf_002.jpg"
        print(f"2. Uploading {test_img.name}...")
        
        file_input = page.locator('input[type="file"]')
        await file_input.set_input_files(str(test_img))
        await page.wait_for_timeout(2000)
        
        # Click Analyse Leaf button
        analyse_btn = page.locator('button:has-text("Analyse Leaf")')
        if await analyse_btn.count() > 0:
            print("3. Clicking 'Analyse Leaf'...")
            await analyse_btn.first.click()
        
        print("4. Waiting for analysis result...")
        result_container = page.locator('[data-testid="stVerticalBlock"]:has-text("Detection Result")')
        await result_container.first.wait_for(timeout=30000)
        await page.wait_for_timeout(2000)
        
        # Take screenshot of the result
        screenshot_path = ARTIFACTS_DIR / "live-model-verified-result.png"
        await page.screenshot(path=str(screenshot_path), full_page=True)
        print(f"5. Saved screenshot to {screenshot_path}")
        
        # Extract page text
        text = await page.content()
        
        # Verify absence of Gemini / Google
        gemini_mentions = [m.start() for m in re.finditer(r'gemini', text, re.IGNORECASE)]
        google_mentions = [m.start() for m in re.finditer(r'google', text, re.IGNORECASE)]
        
        print("\n=== VERIFICATION RESULTS ===")
        print(f"Tomato displayed: {'Tomato' in text}")
        print(f"Early Blight displayed: {'Early Blight' in text}")
        print(f"Immediate Treatment / Care displayed: {'Immediate Treatment' in text or 'Immediate Care' in text}")
        print(f"Prevention displayed: {'Prevention' in text}")
        print(f"Gemini mentions on page: {len(gemini_mentions)}")
        print(f"Google mentions on page: {len(google_mentions)}")
        
        # Also check card headers
        cards = await page.locator('.result-info-card').all_text_contents()
        print(f"Cards found: {len(cards)}")
        for idx, c in enumerate(cards):
            first_line = c.strip().split('\n')[0]
            print(f"  Card {idx+1}: {first_line}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_ui_detection())
