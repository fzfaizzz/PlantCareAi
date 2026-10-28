import json
from pathlib import Path

# Complete catalog for all 8 food-crop classes
catalog_data = [
    {
        "slug": "apple-scab",
        "plant": "Apple",
        "condition": "Apple Scab",
        "class_ids": ["Apple___Apple_scab"],
        "symptoms": [
            "Olive-green to dark brown velvety spots on leaf surfaces.",
            "Deformed, puckered, or curling leaves in severe infections.",
            "Premature defoliation weakening the tree."
        ],
        "care": [
            "Rake and destroy fallen leaves in autumn to eliminate overwintering spores.",
            "Prune canopy branches to improve air circulation and rapid leaf drying.",
            "Apply approved organic copper or sulfur-based bio-fungicides during wet spring periods."
        ],
        "prevention": [
            "Plant resistant apple varieties like Honeycrisp, Liberty, or Enterprise.",
            "Avoid overhead sprinkler irrigation that keeps leaves wet for prolonged hours.",
            "Maintain optimal tree spacing for good sunlight penetration."
        ],
        "sources": [
            {
                "title": "Apple Scab Management in Home Orchards",
                "url": "https://extension.umn.edu/fruit/apple-pest-management",
                "publisher": "University of Minnesota Extension"
            }
        ],
        "reviewed_at": "2026-10-24",
        "attribution": "PlantVillage & University Extension Curated Reference"
    },
    {
        "slug": "corn-common-rust",
        "plant": "Corn",
        "condition": "Common Rust",
        "class_ids": ["Corn___Common_rust", "Corn_(maize)___Common_rust_"],
        "symptoms": [
            "Golden-brown to cinnamon-red pustules on upper and lower leaf surfaces.",
            "Pustules rupture epidermal tissue releasing powdery spores.",
            "Severe infection leads to leaf chlorosis and premature leaf death."
        ],
        "care": [
            "Monitor fields regularly during warm, humid conditions.",
            "Apply foliar fungicides early if rust lesions appear on upper ear leaves before silking.",
            "Harvest silage or grain early if widespread lodging risk develops."
        ],
        "prevention": [
            "Select rust-resistant hybrid corn seeds (Rp gene lines).",
            "Plant early in the season to avoid peak fungal spore arrival.",
            "Practice crop rotation with non-host crops like soybeans."
        ],
        "sources": [
            {
                "title": "Corn Disease Management: Common Rust",
                "url": "https://extension.umn.edu/corn-pest-management/corn-diseases",
                "publisher": "University of Minnesota Extension"
            }
        ],
        "reviewed_at": "2026-10-24",
        "attribution": "PlantVillage & University Extension Curated Reference"
    },
    {
        "slug": "potato-early-blight",
        "plant": "Potato",
        "condition": "Early Blight",
        "class_ids": ["Potato___Early_blight"],
        "symptoms": [
            "Small dark brown to black spots with characteristic concentric rings ('target-board' pattern).",
            "Yellow halo (chlorosis) surrounding the dark lesions.",
            "Older lower leaves infected first, gradually progressing upwards."
        ],
        "care": [
            "Prune and remove severely infected lower foliage to reduce spore load.",
            "Apply copper-based or chlorothalonil fungicides according to weather forecast.",
            "Ensure steady potassium and nitrogen fertility to prevent plant stress."
        ],
        "prevention": [
            "Use certified disease-free potato seed tubers.",
            "Rotate potato fields with non-solanaceous crops on a 3-year cycle.",
            "Use drip irrigation rather than overhead sprinklers to keep foliage dry."
        ],
        "sources": [
            {
                "title": "Potato Early Blight Biology and Management",
                "url": "https://extension.umn.edu/potato-pest-management/early-blight-potatoes",
                "publisher": "University of Minnesota Extension"
            }
        ],
        "reviewed_at": "2026-10-24",
        "attribution": "PlantVillage & University Extension Curated Reference"
    },
    {
        "slug": "potato-late-blight",
        "plant": "Potato",
        "condition": "Late Blight",
        "class_ids": ["Potato___Late_blight"],
        "symptoms": [
            "Water-soaked dark lesions spreading rapidly across leaf tips and margins.",
            "White velvety fungal growth (sporangiophores) on leaf undersides in humid conditions.",
            "Rapid stem rot and foul-smelling foliage decay."
        ],
        "care": [
            "Immediately destroy and bury heavily blighted potato vines to stop spore dispersal.",
            "Apply targeted systemic fungicides (mancozeb, cymoxanil) immediately upon first sighting.",
            "Kill vines 2-3 weeks before harvest to prevent tuber contamination."
        ],
        "prevention": [
            "Plant only certified clean seed potatoes.",
            "Eliminate all cull piles and volunteer potato plants nearby.",
            "Ensure deep hill soil coverage over developing tubers to protect against washed-down spores."
        ],
        "sources": [
            {
                "title": "Late Blight on Potatoes and Tomatoes",
                "url": "https://extension.umn.edu/potato-pest-management/late-blight-potatoes",
                "publisher": "University of Minnesota Extension"
            }
        ],
        "reviewed_at": "2026-10-24",
        "attribution": "PlantVillage & University Extension Curated Reference"
    },
    {
        "slug": "potato-healthy",
        "plant": "Potato",
        "condition": "Healthy",
        "class_ids": ["Potato___healthy"],
        "symptoms": [
            "Lush, uniform green leaf blades with no necrotic spots or halos.",
            "Strong turgid stems and healthy vein architecture.",
            "No visible fungal mycelium, mildew, or insect feeding signs."
        ],
        "care": [
            "Maintain consistent soil moisture without waterlogging the root zone.",
            "Hill soil around plant bases regularly to protect growing tubers from light.",
            "Ensure balanced N-P-K fertilization according to vegetative growth stage."
        ],
        "prevention": [
            "Inspect underside of lower foliage weekly for early pest/disease signs.",
            "Keep potato patch weed-free to improve air circulation and reduce pest vectors.",
            "Clean agricultural tools before pruning or harvesting."
        ],
        "sources": [
            {
                "title": "Growing Potatoes in Home Gardens",
                "url": "https://extension.umn.edu/vegetables/growing-potatoes",
                "publisher": "University of Minnesota Extension"
            }
        ],
        "reviewed_at": "2026-10-24",
        "attribution": "PlantVillage & University Extension Curated Reference"
    },
    {
        "slug": "tomato-early-blight",
        "plant": "Tomato",
        "condition": "Early Blight",
        "class_ids": ["Tomato___Early_blight"],
        "symptoms": [
            "Circular brown lesions with distinct concentric target rings.",
            "Yellowing tissue margins around expanding necrotic spots.",
            "Lower leaves dry up, drop prematurely, exposing fruit to sunscald."
        ],
        "care": [
            "Prune off affected lower leaves up to 12 inches from ground level.",
            "Apply organic neem oil, copper soap, or bio-fungicide at 7-10 day intervals.",
            "Mulch around plant bases to prevent soil-splash onto lower leaves."
        ],
        "prevention": [
            "Practice 3-year crop rotation (avoid planting after potatoes, peppers, eggplants).",
            "Stake or cage tomato plants for vertical growth and superior airflow.",
            "Water solely at the soil base using soaker hoses or drip tape."
        ],
        "sources": [
            {
                "title": "Tomato Early Blight Diagnosis and Control",
                "url": "https://extension.umn.edu/garden-and-home/yard-and-garden/gardening-in-minnesota/yard-and-garden-problems/tomato-leaf-spot-diseases",
                "publisher": "University of Minnesota Extension"
            }
        ],
        "reviewed_at": "2026-10-24",
        "attribution": "PlantVillage & University Extension Curated Reference"
    },
    {
        "slug": "tomato-late-blight",
        "plant": "Tomato",
        "condition": "Late Blight",
        "class_ids": ["Tomato___Late_blight"],
        "symptoms": [
            "Irregular water-soaked greasy brown lesions on leaves and petioles.",
            "White downy spore growth on the underside of leaves during high humidity.",
            "Rapid whole-plant collapse and dark sunken lesions on green or ripe fruits."
        ],
        "care": [
            "Remove and bag infected plant material immediately; do not compost.",
            "Apply copper-based protectant sprays immediately when cool, moist weather threatens.",
            "Harvest remaining unblemished fruits immediately if infection becomes uncontrollable."
        ],
        "prevention": [
            "Select late-blight resistant cultivars (e.g. Mountain Magic, Defiant, Plum Regal).",
            "Avoid overhead irrigation and space plants at least 24-36 inches apart.",
            "Inspect weekly during cool (60-70°F) rainy periods."
        ],
        "sources": [
            {
                "title": "Late Blight Management on Tomatoes",
                "url": "https://extension.umn.edu/vegetables/growing-tomatoes",
                "publisher": "University of Minnesota Extension"
            }
        ],
        "reviewed_at": "2026-10-24",
        "attribution": "PlantVillage & University Extension Curated Reference"
    },
    {
        "slug": "tomato-healthy",
        "plant": "Tomato",
        "condition": "Healthy",
        "class_ids": ["Tomato___healthy"],
        "symptoms": [
            "Vibrant, deep green foliage with uniform leaf coloration.",
            "Crisp leaf margins without wilting, curling, or brown necrotic patches.",
            "Normal vigorous vegetative and reproductive bud development."
        ],
        "care": [
            "Provide 1-1.5 inches of water per week at soil level.",
            "Maintain consistent feeding with high-potassium tomato fertilizer.",
            "Sucker prune indeterminate varieties for optimal air circulation."
        ],
        "prevention": [
            "Maintain 2-3 inches of organic straw or wood-chip mulch around roots.",
            "Scout weekly for aphid or whitefly populations.",
            "Sanitize garden shears with 70% isopropyl alcohol between plants."
        ],
        "sources": [
            {
                "title": "Growing Healthy Tomatoes: Best Practices",
                "url": "https://extension.umn.edu/garden-and-home/yard-and-garden/gardening-in-minnesota/growing-tomatoes",
                "publisher": "University of Minnesota Extension"
            }
        ],
        "reviewed_at": "2026-10-24",
        "attribution": "PlantVillage & University Extension Curated Reference"
    }
]

# Write to both server/catalog.json and plantcare_streamlit/data/catalog.json
p1 = Path("server/catalog.json")
p2 = Path("plantcare_streamlit/data/catalog.json")

p1.write_text(json.dumps(catalog_data, indent=2), encoding="utf-8")
p2.parent.mkdir(parents=True, exist_ok=True)
p2.write_text(json.dumps(catalog_data, indent=2), encoding="utf-8")

print(f"Successfully updated catalog in {p1} and {p2} with {len(catalog_data)} food-crop entries!")
