# PlantCare AI — Reference-Exact UI and Reelmark-Inspired Motion

Implement the existing PlantCare AI React project at `C:\Users\akhta\Downloads\PlantCareAi`. Finish the working website and verify it in a browser. Preserve React, Vite, the existing routes, generated assets, and working request handling. Do not migrate frameworks or replace the project with a static screenshot.

The four supplied PlantCare AI images are the visual authority. Reconstruct those pages, including their spacing, typography, image crops, proportions, botanical framing, annotations, and exact initial compositions. Reelmark is a motion-quality reference only. Do not import its marketplace layout, its 1440 × 1080 coordinates, unrelated copy, product cards, or a ten-video carousel into PlantCare AI.

## Source references and coordinate system

| Route | Source file in C:\Users\akhta\Downloads | Native size | Desktop artboard |
| --- | --- | --- | --- |
| Home | ChatGPT Image Oct 21, 2026, 06_51_58 PM.png | 1586 × 992 | 1586 × 992 |
| Library | ChatGPT Image Oct 21, 2026, 06_51_36 PM.png | 1536 × 1024 | 1536 × 1024 |
| Detect | ChatGPT Image Oct 21, 2026, 06_51_21 PM.png | 657 × 435 | 1314 × 870, exactly 2× native |
| About | ChatGPT Image Oct 21, 2026, 06_51_05 PM.png | 1536 × 1024 | 1536 × 1024 |

All coordinates below are `x, y, width, height`, measured from the image's top-left. Detect coordinates are native 657 × 435; double every Detect coordinate and font size for its 1314 × 870 desktop artboard.

Use `qa/reference-measurements.json` as the detailed measurement record. Major boxes were measured to approximately ±2 native pixels; rotated foliage and card edges to ±4 pixels. Font sizes are raster estimates, not recovered font metadata. Confirm typography by overlaying the browser render, matching line breaks and glyph extents.

For available widths of 821 CSS pixels and above, define a per-route unit `--u = availableWidth / routeArtboardWidth`. Scale that route's desktop geometry uniformly from its own artboard. Scale horizontal and vertical positions, dimensions, font sizes, radii, and gaps together. Do not use viewport height to squeeze the composition. The measured artboard may extend below the viewport and the document must remain scrollable.

At 820 CSS pixels and below, use a separate mobile reflow. Do not shrink the whole desktop screenshot into an unreadable thumbnail.

## Shared visual rules

Use the screenshots' warm off-white background, forest green, pale sage, restrained shadows, and softly lit botanical atmosphere. Start from background `#F5F8EF`, forest `#08482D`, dark green `#0B5037`, mint `#DAE7C7`, sage `#EAF1DE`, text `#101410`, secondary text `#5E5E61`, and border `#DCE7D0`; refine against the reference pixels.

Use Inter Tight for bold headings, Inter for interface text, and Caveat for handwritten notes. Use the installed font packages' actual existing entry files. Wait for fonts before screenshot verification.

Keep the shared header component, with route-specific artboard sizing where the source screenshots differ. Preserve the brand, Home, Detect Disease, Plant Library, How It Works, About, Log in, and Sign up. Match the selected navigation pill on each route. Keep a working accessible mobile menu.

Do not add new visible headings, helper paragraphs, navigation, carousel arrows, cards, banners, panels, or decorative sections to the reference frames. Existing functional status or error messages may appear when their relevant state occurs. Keep any existing footer below the reference composition if it would otherwise occupy space absent from the source screenshot.

Simple icons, handwritten arrows, connecting lines, focus markers, and scan overlays may use SVG/CSS. Realistic leaves, plants, botanical decorations, and disease symptoms must use actual image files.

## Home: 1586 × 992 artboard

### Header and hero

| Element | Native box or anchor |
| --- | --- |
| Brand | 97, 23, 207, 42 |
| Brand icon | 97, 23, 39, 42 |
| Wordmark | 145, 31, 159, 29 |
| Active Home pill | 484, 23, 89, 39 |
| Navigation label centers | Home 528/43; Detect 649/43; Library 788/43; How It Works 922/43; About 1034/43 |
| Log in | 1246, 19, 106, 47 |
| Sign up | 1370, 19, 114, 48 |
| AI-powered plant health badge | 664, 115, 257, 43 |
| Heading layout | 361, 171, 873, 177 |
| Heading first-line ink | 414, 183, 784, 63 |
| Heading second-line ink | 365, 267, 863, 80 |
| Subtitle | 495, 366, 604, 52; line tops 366 and 398 |
| CTA button | 665, 839, 257, 69 |
| CTA dashed outline | 656, 831, 275, 85 |

Use the exact two-line headline:

> Detect Plant Diseases  
> with a Single Leaf Photo

Use approximately 83px heading text, 85px line height, weight 780, and tight tracking at native size. Match the raster line widths before accepting the heading. Navigation is approximately 16px; brand 29px; subtitle 22px with 32px line height; CTA 20px.

Use the screenshot's supporting text:

> Upload a leaf image to identify supported plant diseases,  
> explore symptoms, and discover helpful plant-care guidance.

Place “Scan a leaf” around 1346/279, its arrow around 1310/329, the headline strokes around 295/315, “Free to try” around 510/873, and its short arrow around 587/840. Preserve the notes' handwritten character and direction.

Frame the page with separately generated foliage: upper-left visible area about −18/35/207/266, upper-right 1330/93/256/265, lower-left −20/831/374/161, lower-right 1274/840/312/152. Match crop and blur, not just the presence of green imagery.

### Seven-card initial carousel composition

Use exactly these seven individual photographic assets and labels in this order:

| Card | Label | Visible native bounds |
| --- | --- | --- |
| 1 | Tomato / Healthy | −2, 425, 216, 378 |
| 2 | Tomato / Early Blight | 230, 448, 213, 341 |
| 3 | Potato / Late Blight | 459, 462, 211, 318 |
| 4 | Apple / Apple Scab | 687, 468, 212, 308 |
| 5 | Corn / Common Rust | 915, 464, 212, 315 |
| 6 | Grape / Powdery Mildew | 1143, 451, 215, 337 |
| 7 | Explore / More Plants | 1376, 423, 212, 381 |

The edge cards are partly clipped and taller in the reference composition. Match the gentle arc and perspective instead of substituting a flat row of equal-height boxes. Use roughly 17px gaps, 15px corners, 42px frosted play circles, 18px plant labels, and 14px condition labels. Keep the bottom gradients and label alignment.

The play-shaped mark is the reference's icon. It must not imply that a generated still photo is an actual playable video. Clicking a plant opens its library detail; Explore opens the library.

## Library: 1536 × 1024 artboard

| Element | Native box or anchor |
| --- | --- |
| Brand | 182, 17, 203, 37 |
| Active Plant Library pill | 693, 16, 129, 40 |
| Log in / Sign up | 1189,16,94,40 / 1297,16,106,40 |
| Badge | 657, 79, 224, 39 |
| Heading layout / ink | 469,125,625,74 / 470,134,621,64 |
| Subtitle | 410, 205, 717, 24 |
| Search field | 209, 244, 887, 48 |
| Plant dropdown | 1112, 244, 220, 48 |
| Category row | y310, height46 |
| Grid | x45, y377; 5 columns of274; approximately20px column gap |
| Column starts | 45, 339, 632, 925, 1218 |
| Row starts | 377, 689 |
| Card height / row gap | 294 / 18 |
| Card info top | card y +184; info height110 |

Use “Explore plant knowledge”, “Plant Disease Library”, and the screenshot's subtitle. Heading is approximately 66px, weight780, 74px line height. Subtitle 19px. Search and chip text 16px.

Chip x positions and widths:

| All | Tomato | Potato | Apple | Corn | Grape | Pepper | Strawberry | Healthy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 84 /121 | 219 /137 | 369 /127 | 509 /124 | 646 /114 | 773 /126 | 913 /136 | 1062 /165 | 1241 /155 |

Match the screenshot's two rows of cards: Tomato Healthy; Tomato Early Blight; Tomato Late Blight; Potato Healthy; Potato Late Blight; Apple Apple Scab; Apple Black Rot; Corn Healthy; Corn Common Rust; Grape Powdery Mildew. The third card's visible reference label is Late Blight; the older master prompt's Leaf Spot example is not the raster's literal label. Ensure the entry identity, image, and text agree. Do not claim any library entry is a verified model class without implementation evidence.

Card details: 15px radius; status pill offset13/11, height31, font14; titles approximately16px/21px; description13px/18px; circular arrow39px at card offset224/204. Use the soft translucent bottom panel overlapping the photograph. Preserve the distinctive image crop in each card.

Search by plant, condition, and visible symptoms. Category and dropdown filters must work together predictably. Include a real empty result state, live result announcement, and a clear-search control that restores input focus. A card must open an accessible detail view with relevant available information; Escape, backdrop dismissal, and focus restoration must work.

## Detect: native657 × 435, implemented at1314 × 870

| Element | Native box or anchor; multiply by2 |
| --- | --- |
| Brand | 62, 8, 97, 21 |
| Active Detect pill | 243, 8, 72, 22 |
| Log in / Sign up | 526,7,48,23 / 583,7,56,23 |
| Badge | 269, 43, 125, 20 |
| Heading layout | 189, 69, 285, 60 |
| First / second heading ink | 197,74,271,23 / 191,103,281,25 |
| Subtitle | 212, 139, 239, 23 |
| Upload panel | 197, 181, 269, 153 |
| Cloud icon | 315, 204, 33, 27 |
| Upload heading | 254, 242, 156, 12 |
| Browse support text | 282, 261, 100, 9 |
| Choose Image button | 256, 279, 150, 28 |
| Supported-file text | 263, 316, 137, 7 |
| Privacy row | 233, 345, 198, 11 |
| Feature strip | approximately65, 372, 558, 47 |
| Feature icons | 83/380,264/380,445/380; each31 ×31 |

Native heading size is approximately27px/29px; subtitle8.5px/12px; upload heading11px; button9px; supported and privacy text7px. These become54px/58px,17px/24px,22px,18px,14px on the2× desktop artboard.

Use the exact two-line main heading and the reference's badge. The initial upload panel must be visually centered at x331.5 native. Use a pale sage surface, 11px native corners, a fine dashed green border, cloud icon, “Drag & drop a leaf image here”, “or click to browse files”, and Choose Image.

The three sample photo bounds are56/194/72/88 at about−8°,124/182/57/70 at about10°, and99/248/58/68 at about−8°. Use separate image files. The “Upload a leaf” annotation is around105/136; its arrow153/149. The large right botanical visual occupies about511/49/146/333. The right handwritten note occupies494/270/59/56.

Feature text starts x121,303,485; titles y385, subtitles y399. Preserve this spacing. The screenshot's “38+ Plant Diseases” is not evidence of an implemented disease count: only render a count if verified, otherwise make the smallest truthful content exception inside the same geometry.

### Actual upload and request lifecycle

Keep the initial screenshot composition intact. After a user selects an image:

1. Validate the accepted type, size, and actual decodability.
2. Show that actual selected image, centered without stretching.
3. Allow replacement/removal.
4. Submit only to a real configured analysis endpoint.
5. Enter pending state while that real request is unresolved.
6. Run the scan overlay only during that pending state.
7. Stop immediately on response, failure, cancellation, or unmount.
8. Display only real returned data or a clear error.

Use an explicit lifecycle such as idle → selected → uploading/analyzing → success/error. Do not use a fixed timeout, fabricated result, confidence, diagnosis, or artificial completion event.

The scan is a thin horizontal green beam over the actual preview, with subtle glow, translucent overlay, four corner markers, and a readable pending status. The preview remains visible. Reduced motion keeps the status and markers understandable while removing beam travel.

If no backend is configured, retain a clearly identified UI demonstration and do not present generated samples or local visual checks as medical/agricultural analysis. Match the page's reference geometry; place necessary truthful operational copy where it is relevant to the upload state, without inventing a new prominent panel.

Do not claim uploads are never stored or that data stays private unless the implemented request/storage behavior supports that promise.

## About: 1536 × 1024 artboard

| Element | Native box or anchor |
| --- | --- |
| Brand | 203, 15, 187, 36 |
| Active About pill | 924, 14, 82, 38 |
| Log in / Sign up | 1157,14,88,38 / 1258,14,100,38 |
| Badge | 254, 89, 171, 35 |
| Heading layout | 254, 135, 407, 109 |
| First / second heading ink | 255,142,356,41 / 254,199,399,41 |
| Description | 254, 265, 430, 103 |
| Primary / secondary CTA | 254,390,222,48 / 491,390,190,48 |
| Community avatar row | 254, 455, 105, 32 |
| Community text | 374, 465, 309, 14 |
| Main botanical image | approximately764, 109, 589, 383 |
| Soft circular backdrop | 877, 94, 398, 400 |
| Right handwritten note | 1276, 104, 148, 120 |
| Hero bottom separator | y517 |

Use “Our Purpose is” followed by green “Healthier Plants”. Approximate native typography: heading54px/57px, weight780; description15px/22px; buttons14px; community text13px. Keep the left copy width and the screenshot's five description lines. Preserve the right hero's large natural leaves and the callout around766/365 with its short connecting line.

Mission, Vision, and Values occupy the next horizontal band beginning y517. Icons are74 ×74 at155/549,612/549,1057/549. Headings start255/557,713/557,1159/557 at21px. Body begins y592 at13px/20px. Vertical separators stand at x574 and1019, from y549 to667. Preserve the three-column composition.

Technology heading is140/719, about24px; its supporting text140/752,13px. Six reference tile slots occupy y712–815 with boxes425/712/136/103,572/712/134/103,716/712/139/103,866/712/147/103,1026/712/157/103,1193/712/159/103. Icons begin around y728,29px. Names begin y770 at12px; subtitles y789 at11px.

The reference labels Python, TensorFlow, OpenCV, React, FastAPI, and Tailwind CSS are visual observations, not proof of the current stack. Do not claim unused technology is implemented. Preserve the measured strip and use only verified implementation details, with the smallest explicit truthful content exception required.

Bottom supporting photo begins0/820 with585px width and27px top corners; the reference shows204px of it. Its white overlaid copy starts70/913,18px. The Dataset & Model panel begins612/827 with924px visible width. Heading645/848 at24px; subtitle646/878 at13px. Two circular icons are665/912/73/73 and1089/912/73/73. Article title x positions766 and1194 at y916; body begins y939 at13px/18px.

The source's PlantVillage,54,000+ images, CNN, and accuracy implications must not become false implementation claims. Describe the actual verified dataset/analysis architecture while retaining the reference section's dimensions and hierarchy. Do not replace the entire section with a different layout.

## Assets: actual files, individually generated

Reuse the already generated, inspected assets wherever they match the required crop. Generate only genuinely missing or unsuitable assets, one image per required purpose using the available built-in image tool. Save every selected image in the project, optimize for web delivery, preserve original PNGs outside public, and update the asset manifest with real paths.

The home carousel requires seven separate photographs, not ten unrelated video clips and not a collage cropped into seven assets. The library requires its own distinct plant/condition compositions. Detect uses its three separate sample photos and its right botanical decoration. About uses its dedicated large botanical hero and supporting photo.

Do not fabricate botanical subjects with CSS, SVG, Canvas, gradients, polygons, emoji, or procedural geometry. CSS may position, crop, blur, shade, and animate actual images. Generated symptom images are illustrative; they are not authenticated scientific specimens or validated training data.

No video-generation capability is established for this task. Do not claim that videos were generated. Use photographic card motion to provide Reelmark-style polish. If actual video files are later explicitly supplied and requested, integrate them truthfully and preserve the reference layout.

## Reelmark-inspired motion without changing the PlantCare composition

Reproduce the measured still composition first. Add motion on separate transform layers so entrance, arc/perspective, hover, and track translation do not overwrite one another.

Use a short coordinated sequence: header fades with slight downward settling; badge appears gently; headline lines rise a few pixels with restrained blur-to-sharp; supporting text fades; foliage and handwritten notes settle; arrow strokes draw; cards rise into their measured positions with a small stagger; CTA appears. Keep controls usable throughout. Do not make the user wait for an animation to finish.

The carousel needs time-based requestAnimationFrame movement, gentle continuous drift, real pointer/touch dragging, velocity estimation, momentum, friction, and a smooth return to automatic drift. Pause automatic drift during hover/focus/interaction while allowing intentional drag momentum to settle. Keep seven logical entries and seamless visual track wrapping. No visible jump, sudden snap, or frame-rate-dependent speed.

Card activation must work for ordinary mouse clicks, touch taps, and keyboard Enter. Capture a pointer only after a drag threshold is crossed; suppress only the click generated by that drag. Clear suppression on pointer cancellation and do not suppress keyboard-generated clicks. Track the active pointer ID and handle lost capture.

Cloned loop groups must never create duplicate keyboard stops or screen-reader content, and visible clones must remain correctly clickable. Do not make visible cards inert. Keep the keyboard-focused logical card visible. Pause drift while keyboard focus is in the carousel.

Use restrained image zoom, card lift, shadow change, and arrow movement on hover. Float peripheral botanical images slowly at low amplitude. Keep annotations readable and do not move foliage over controls.

Pause nonessential continuous motion when the document is hidden; clean up observers, listeners, pointer capture, and animation frames. Respect reduced motion: freeze automatic drift, remove large entrances/blur/parallax, preserve every interaction, and convey pending analysis through text and static markers.

## Responsive behavior and accessibility

At desktop artboard widths, the four supplied images are the exact geometry targets. At mobile widths320,390, and768, independently reflow: compact accessible navigation; readable heading; touch-draggable carousel; horizontal chips; practical two-column or one-column cards; full-width upload panel; stacked About hero and sections. Use comfortable touch targets and no unintended page overflow.

Keep visible focus, semantic controls, form labels, live search/pending/error announcements, and meaningful image alternatives. Decorative foliage is hidden from assistive technology.

Use native dialog behavior or an equivalent complete modal implementation. Opening focuses an appropriate control, background content becomes unavailable, Tab remains inside, Escape closes, and close restores the originating control. Backdrop dismissal requires a gesture that starts and ends on the backdrop. Do not dismiss when a selection begins inside the dialog and ends outside.

Preserve honest existing account behavior. Do not make Log in/Sign up appear to create an online account when no authentication service exists.

## Verification and completion

Do not accept “similar” as the final desktop result. For every route:

1. Render at the corresponding native artboard size; render Detect at1314 ×870 and compare to a2× reference.
2. Wait for assets/fonts and freeze decorative animation at the intended initial settled composition.
3. Save a full viewport screenshot.
4. Generate a50% reference/render overlay and an absolute difference image.
5. Inspect header positions, headline line breaks and widths, subtitle baselines, all major boxes, card boundaries, crop, CTA, and section boundaries.
6. Correct the implementation and repeat until the major measured geometry is within approximately2 native pixels; record any residual mismatch, especially image-content differences, honestly.
7. Test the same route at available widths1440,1024,821,820,768,390, and320 as applicable. Desktop scaling must retain the source proportions; mobile must reflow.
8. Test ordinary card clicks, drag release, touch-style gestures, keyboard activation, clone seam behavior, search, all filters, clear focus, modal keyboard lifecycle, file validation, cancellation, pending success/error, and reduced motion.
9. Run the project's meaningful tests and production build; inspect for broken image requests and browser errors.

Keep a concise QA record with actual screenshots/overlays, executed checks, and unresolved differences. Do not claim screenshot-level fidelity, a generated file, a working API, or a passing test without evidence.

Deliver the updated working project, real saved assets, this updated project prompt, the measurement record, run instructions, and a candid concise account of what was verified and what remains unavailable.

