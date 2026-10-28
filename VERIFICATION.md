# Verification — corrected reference layout

Verified on 22 October 2026 in installed Google Chrome.

- Final production build: PASS. 36 real, nonempty WebP assets; 5.43 MB total.
- Native reference anchors: 10 groups PASS within 2 CSS pixels for their measured boxes. Home badge/CTA, Library search/grid, Detect panel, About badge/CTA/mission/technology/dataset.
- Responsive bounds: 28 route checks PASS across the four reference pages at 1440, 1024, 821, 820, 768, 390 and 320 pixels. No document overflow or browser page errors.
- Main browser interactions: 8 groups PASS, including search, filters, dialogs, pointer drag, card clicks, mobile navigation, actual image previews, profile persistence and reduced motion.
- Curved carousel: seven source photographs; rounded quads recomputed from current position; independently varying edge heights; measured auto drift exactly 50 native units/second. Mouse drag and momentum verified.
- Touch regression: all 8 real touch moves follow the full 15, 30, 45, 60, 75, 90, 105 and 120 pixels before release. The capture-transfer bug is fixed.
- Scan lifecycle: 10 browser groups PASS with explicit controlled HTTP fixtures. Beam exists only during the pending request and stops on settlement/cancel/removal/navigation.
- Long-result regression at 1314 pixels: uploader ends at y1653.156; features begin at y1683.156, leaving exactly 30 pixels. Full prevention guidance, disclaimer and restart control remain visible; page ends at y1809.156.
- Invalid-file regression: error, privacy and demo messages remain separate; the page expands without overlap.
- Existing analysis validation/request unit suite: 11 PASS. Its implementation is unchanged in this correction.
- Test-only servers stopped. The existing user preview at http://127.0.0.1:5173 was reused.

## Evidence

- `qa/reference-measurements.json`: source measurements.
- `qa/reference-v2/measurements.json`: final native boxes and responsive checks.
- `qa/reference-v2/*.png`: corrected original-size renders and responsive screenshots.
- `qa/reference-v2/*-overlay.png`: 50% source/current comparison overlays.
- `qa/browser-report.json`: interaction results.
- `qa/scan-browser-results.json`: controlled request lifecycle checks.
- `qa/scan-regression-results.json`: full touch and long-result regression evidence.
- `qa/scan-pending.png`, `qa/scan-results-1314.png`: selected photo and scan/results examples from explicit test fixtures.

## What changed

`src/reference.css` now uses each source screenshot's own artboard instead of one generic content grid. Header sizing/positions are route-specific. Main page anchors are measured, including the About copy at x254 and the Library grid at y377. Headline glyph extents were compared against reference pixels and adjusted. The carousel uses dynamic sloping quads rather than rotated rectangles. Six technology slots and the original About section geometry are restored, with actual implementation labels.

Seven new reference-oriented asset generations/refinements were saved separately. The final wide About branch and lower botanical photo use the specific reference composition as input. No screenshot is used as the application background, and final botanical assets are not crops of a composite UI.

## Limits

The source photographs were recreated with ImageGen, so this is not a claim of identical photographic pixels. Font metadata was estimated from raster images and measured in the browser. Semantic copy avoids unverified supported-class counts, trained-model/dataset claims and online authentication. Live diagnosis remains clearly marked as unconnected; controlled scan fixtures establish UI lifecycle behavior, not diagnostic accuracy.

Run instructions and file list: `README.md`. Reusable revised prompt: `UPDATED-PROJECT-PROMPT.md`.
