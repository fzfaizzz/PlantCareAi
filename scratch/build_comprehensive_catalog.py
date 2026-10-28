"""
Update server/catalog.json with comprehensive, practical, crystal-clear
disease symptoms, immediate actions, organic care, and long-term prevention.
Written in easy-to-understand language for both agricultural practical use and college viva defense.
"""
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
CATALOG_PATH = BASE_DIR / "server" / "catalog.json"

CATALOG_DATA = [
    {
        "slug": "tomato-early-blight",
        "plant": "Tomato",
        "condition": "Early Blight (Alternaria solani)",
        "scientific_name": "Solanum lycopersicum",
        "class_ids": ["Tomato___Early_blight"],
        "severity": "Moderate to High",
        "symptoms": [
            "Dark brown circular spots with characteristic concentric rings (target-board pattern).",
            "Yellow halo (chlorosis) surrounding necrotic lesions on older leaves.",
            "Lower foliage turns yellow, withers, and drops prematurely."
        ],
        "care": [
            "Prune and safely dispose of infected lower foliage immediately; do NOT compost them.",
            "Water exclusively at soil level using drip or furrow irrigation; keep leaves completely dry.",
            "Apply organic copper fungicide or 0.5% cold-pressed neem oil spray every 7–10 days."
        ],
        "prevention": [
            "Apply a 2–3 inch layer of organic straw mulch around plant stems to stop soil spore splash.",
            "Maintain 24–36 inches plant spacing to ensure rapid leaf drying and optimal airflow.",
            "Practice 3-year crop rotation; avoid planting tomatoes after potatoes, peppers, or eggplants."
        ],
        "sources": [
            {
                "title": "University of Minnesota Extension - Tomato Early Blight Management",
                "url": "https://extension.umn.edu/diseases/early-blight-tomato",
                "publisher": "UMN Extension"
            }
        ],
        "reviewed_at": "2026-10-24",
        "attribution": "Agricultural Research & Extension Plant Pathology Database"
    },
    {
        "slug": "tomato-late-blight",
        "plant": "Tomato",
        "condition": "Late Blight (Phytophthora infestans)",
        "scientific_name": "Solanum lycopersicum",
        "class_ids": ["Tomato___Late_blight"],
        "severity": "Critical / Fast-Spreading",
        "symptoms": [
            "Irregular, water-soaked dark brown to purplish lesions rapidly expanding across leaves.",
            "Delicate white fungal down/mold visible on the underside of leaves during humid weather.",
            "Rapid leaf collapse and browning that spreads through entire branches within days."
        ],
        "care": [
            "Immediately bag and remove severely infected branches to prevent airborne spore spread.",
            "Spray bio-fungicide (Bacillus subtilis) or organic copper-soap solution on healthy foliage.",
            "Ensure plants receive full sunlight and stop all overhead sprinkling immediately."
        ],
        "prevention": [
            "Plant certified disease-resistant tomato varieties (such as Defiant or Mountain Merit).",
            "Eliminate volunteer tomato and weed nightshade plants around the growing area.",
            "Sanitize pruning shears with 70% isopropyl alcohol between every plant."
        ],
        "sources": [
            {
                "title": "Cornell University Vegetable Pathology - Tomato Late Blight Guide",
                "url": "https://www.vegetables.cornell.edu/pest-management/disease-factsheets/late-blight/",
                "publisher": "Cornell University"
            }
        ],
        "reviewed_at": "2026-10-24",
        "attribution": "Agricultural Research & Extension Plant Pathology Database"
    },
    {
        "slug": "tomato-healthy",
        "plant": "Tomato",
        "condition": "Healthy Foliage",
        "scientific_name": "Solanum lycopersicum",
        "class_ids": ["Tomato___healthy"],
        "severity": "None (Healthy)",
        "symptoms": [
            "Leaves display rich, uniform emerald green pigmentation across the blade.",
            "Leaf margins and veins are intact with strong turgor pressure and zero necrotic spotting.",
            "Normal upright growth habit free of fungal fuzz, pest damage, or chlorosis."
        ],
        "care": [
            "Maintain consistent deep watering (1–2 inches weekly) directly into the root zone.",
            "Feed with balanced organic compost tea or phosphorus/potassium-rich tomato fertilizer.",
            "Stake or cage plants upright to keep foliage well above damp soil."
        ],
        "prevention": [
            "Inspect leaf undersides once a week for early signs of aphids or fungal spores.",
            "Maintain clean organic mulch to regulate soil moisture and root temperatures.",
            "Ensure plants receive 6–8 hours of uninterrupted daily sunlight."
        ],
        "sources": [
            {
                "title": "Penn State Extension - Growing Healthy Tomatoes",
                "url": "https://extension.psu.edu/growing-tomatoes",
                "publisher": "Penn State Extension"
            }
        ],
        "reviewed_at": "2026-10-24",
        "attribution": "Agricultural Research & Extension Plant Pathology Database"
    },
    {
        "slug": "potato-early-blight",
        "plant": "Potato",
        "condition": "Early Blight (Alternaria solani)",
        "scientific_name": "Solanum tuberosum",
        "class_ids": ["Potato___Early_blight"],
        "severity": "Moderate",
        "symptoms": [
            "Small, scattered dark brown spots developing concentric ring patterns on mature foliage.",
            "Surrounding leaf tissue turns yellow, causing lower leaves to curl upward and dry out.",
            "Stems develop elongated brown lesions as the fungal infection progresses."
        ],
        "care": [
            "Cut away infected lower leaves touching damp soil with clean pruning shears.",
            "Apply organic copper fungicide or bio-based neem spray during early morning hours.",
            "Cease sprinkler irrigation; use furrow or drip lines to keep canopy dry."
        ],
        "prevention": [
            "Hill potatoes with clean, fresh soil and organic straw mulch to protect tubers.",
            "Rotate fields with non-solanaceous crops (beans, corn, wheat) for at least 3 years.",
            "Harvest tubers only after vines have completely matured and skin has set firmly."
        ],
        "sources": [
            {
                "title": "University of Idaho Extension - Potato Early Blight Management",
                "url": "https://www.extension.uidaho.edu/publishing/pdf/CIS/CIS1089.pdf",
                "publisher": "University of Idaho"
            }
        ],
        "reviewed_at": "2026-10-24",
        "attribution": "Agricultural Research & Extension Plant Pathology Database"
    },
    {
        "slug": "potato-late-blight",
        "plant": "Potato",
        "condition": "Late Blight (Phytophthora infestans)",
        "scientific_name": "Solanum tuberosum",
        "class_ids": ["Potato___Late_blight"],
        "severity": "Critical / Highly Contagious",
        "symptoms": [
            "Pale green water-soaked spots rapidly expanding into large dark brown/black necrotic blotches.",
            "White cottony fungal growth on lower leaf surfaces during cool, high-humidity weather.",
            "Distinct musty odor as foliage rots and collapses in severe outbreaks."
        ],
        "care": [
            "Prune and safely destroy infected foliage immediately; burning or deep burying.",
            "Spray protective copper-hydroxide fungicide over healthy foliage to block spore germination.",
            "Improve field surface drainage and cease all overhead irrigation immediately."
        ],
        "prevention": [
            "Plant only certified disease-free seed tubers from verified agricultural suppliers.",
            "Destroy all cull potato piles and volunteer potato sprouts before planting season.",
            "Allow vines to completely die for 2 weeks before digging to prevent tuber inoculation."
        ],
        "sources": [
            {
                "title": "Michigan State University - Potato Late Blight Protection",
                "url": "https://www.canr.msu.edu/resources/potato_late_blight",
                "publisher": "MSU Extension"
            }
        ],
        "reviewed_at": "2026-10-24",
        "attribution": "Agricultural Research & Extension Plant Pathology Database"
    },
    {
        "slug": "potato-healthy",
        "plant": "Potato",
        "condition": "Healthy Foliage",
        "scientific_name": "Solanum tuberosum",
        "class_ids": ["Potato___healthy"],
        "severity": "None (Healthy)",
        "symptoms": [
            "Foliage is vibrant green, firm, and fully expanded without discoloration or chlorosis.",
            "Smooth leaf surface free of necrotic lesions, powdery mildew, or curled edges.",
            "Vigorous upright growth habit with strong stem development."
        ],
        "care": [
            "Provide consistent soil moisture (about 1 inch per week) during tuber initiation.",
            "Hill up loose soil around stems when plants reach 8–10 inches in height.",
            "Apply balanced potassium-rich organic fertilizer to support healthy tuber bulking."
        ],
        "prevention": [
            "Scout fields twice weekly during cool, damp weather for early warning signs.",
            "Maintain wide row spacing (30–36 inches) for continuous air movement.",
            "Store harvested potatoes in a cool, dry, well-ventilated dark cellar."
        ],
        "sources": [
            {
                "title": "Oregon State University - Potato Production Guide",
                "url": "https://extension.oregonstate.edu/crop-production/potatoes",
                "publisher": "OSU Extension"
            }
        ],
        "reviewed_at": "2026-10-24",
        "attribution": "Agricultural Research & Extension Plant Pathology Database"
    },
    {
        "slug": "corn-common-rust",
        "plant": "Corn",
        "condition": "Common Rust (Puccinia sorghi)",
        "scientific_name": "Zea mays",
        "class_ids": ["Corn___Common_rust"],
        "severity": "Moderate",
        "symptoms": [
            "Small, raised cinnamon-brown to golden-red pustules on both upper and lower leaf surfaces.",
            "Pustules rupture the leaf epidermis, releasing powdery rusty-brown spores when touched.",
            "Severe cases cause leaves to yellow, dry out, and scorch prematurely."
        ],
        "care": [
            "Remove severely infected lower corn leaves if infection is localized to bottom canopy.",
            "Apply sulfur-based or copper fungicide if rust appears before the tasseling stage.",
            "Ensure morning dew evaporates quickly by removing weeds that impede airflow."
        ],
        "prevention": [
            "Plant resistant or tolerant corn hybrids with proven rust resistance genes (Rp genes).",
            "Plant early in the season to allow ears to develop before peak rust spore migration.",
            "Incorporate crop residues into soil post-harvest to speed up decomposition."
        ],
        "sources": [
            {
                "title": "Iowa State University Extension - Common Rust on Corn",
                "url": "https://crops.extension.iastate.edu/cropnews/2020/07/common-rust-corn",
                "publisher": "Iowa State Extension"
            }
        ],
        "reviewed_at": "2026-10-24",
        "attribution": "Agricultural Research & Extension Plant Pathology Database"
    },
    {
        "slug": "corn-healthy",
        "plant": "Corn",
        "condition": "Healthy Foliage",
        "scientific_name": "Zea mays",
        "class_ids": ["Corn___healthy"],
        "severity": "None (Healthy)",
        "symptoms": [
            "Broad, elongated arching leaves showing deep green coloration and smooth leaf blades.",
            "Strong central midrib and vascular veins without discoloration or yellow striping.",
            "Uniform upright stalk development with vigorous vegetative growth."
        ],
        "care": [
            "Ensure regular irrigation (1–1.5 inches weekly), especially critical during silking and tasseling.",
            "Apply nitrogen-rich organic side dressing when stalks reach knee-high.",
            "Keep soil aerated and weed-free around the base of the stalks."
        ],
        "prevention": [
            "Maintain optimal row spacing (30 inches) to prevent excessive humidity pockets.",
            "Rotate crops annually with nitrogen-fixing legumes like soybeans.",
            "Monitor leaves bi-weekly for armyworms and early rust pustules."
        ],
        "sources": [
            {
                "title": "Purdue University Extension - Corn Growth & Management",
                "url": "https://www.agry.purdue.edu/ext/corn/",
                "publisher": "Purdue Extension"
            }
        ],
        "reviewed_at": "2026-10-24",
        "attribution": "Agricultural Research & Extension Plant Pathology Database"
    },
    {
        "slug": "apple-scab",
        "plant": "Apple",
        "condition": "Apple Scab (Venturia inaequalis)",
        "scientific_name": "Malus domestica",
        "class_ids": ["Apple___Apple_scab"],
        "severity": "Moderate to High",
        "symptoms": [
            "Olive-green to velvety dark brown circular lesions on upper leaf surfaces.",
            "Lesions turn dark brown to black and develop a corky, scabby texture over time.",
            "Infected leaves buckle, curl, turn yellow, and drop prematurely in mid-summer."
        ],
        "care": [
            "Rake and thoroughly remove all fallen apple leaves and twigs beneath trees.",
            "Spray wettable sulfur, neem oil, or potassium bicarbonate at green tip and petal fall.",
            "Prune tree canopies in late winter to open the center for sunlight and wind penetration."
        ],
        "prevention": [
            "Choose scab-resistant cultivars (e.g., Liberty, Freedom, Enterprise, Prima).",
            "Apply compost tea or urea in late autumn to accelerate the breakdown of fallen leaves.",
            "Avoid planting apple trees in sunken, low-lying frost pockets with poor air movement."
        ],
        "sources": [
            {
                "title": "Ohio State University Extension - Apple Scab Control",
                "url": "https://ohioline.osu.edu/factsheet/plpath-fru-23",
                "publisher": "OSU Extension"
            }
        ],
        "reviewed_at": "2026-10-24",
        "attribution": "Agricultural Research & Extension Plant Pathology Database"
    },
    {
        "slug": "apple-black-rot",
        "plant": "Apple",
        "condition": "Black Rot (Botryosphaeria obtusa)",
        "scientific_name": "Malus domestica",
        "class_ids": ["Apple___Black_rot"],
        "severity": "High",
        "symptoms": [
            "Small purple spots expanding into circular lesions with tan centers (frog-eye leaf spot).",
            "Concentric rings visible on older leaf spots with distinct purple margins.",
            "Heavily infected leaves turn yellow and drop, weakening tree vigor."
        ],
        "care": [
            "Prune out dead wood, fire blight strikes, and cankers at least 6–8 inches below damage.",
            "Remove all mummified fruit remaining on the tree or ground during winter dormancy.",
            "Apply protective copper or captan spray from tight cluster through mid-summer."
        ],
        "prevention": [
            "Maintain overall tree health through balanced fertilization and proper pruning.",
            "Sanitize pruning tools between cuts with 70% alcohol or bleach solution.",
            "Ensure proper drainage and adequate spacing to promote rapid foliage drying."
        ],
        "sources": [
            {
                "title": "Penn State Extension - Apple Black Rot",
                "url": "https://extension.psu.edu/apple-disease-black-rot",
                "publisher": "Penn State Extension"
            }
        ],
        "reviewed_at": "2026-10-24",
        "attribution": "Agricultural Research & Extension Plant Pathology Database"
    },
    {
        "slug": "grape-powdery-mildew",
        "plant": "Grape",
        "condition": "Powdery Mildew (Erysiphe necator)",
        "scientific_name": "Vitis vinifera",
        "class_ids": ["Grape___Powdery_mildew"],
        "severity": "Moderate to High",
        "symptoms": [
            "White to dusty-gray powdery fungal patches appearing on upper and lower leaf surfaces.",
            "Leaves may become distorted, crinkled, or curled upwards.",
            "Severe infections cause leaves to yellow, dry out, and drop prematurely."
        ],
        "care": [
            "Apply potassium bicarbonate or horticultural neem oil spray at first sign of powdery dust.",
            "Prune dense canopy and shoot-thin to maximize sunlight penetration into the vine interior.",
            "Avoid excessive nitrogen fertilization, which produces overly dense, susceptible young foliage."
        ],
        "prevention": [
            "Trellis vines to ensure open canopy airflow and direct sunlight on all clusters.",
            "Apply dormant lime sulfur spray before spring bud break to reduce overwintering chasmothecia.",
            "Plant resistant grape cultivars suited to your regional climate."
        ],
        "sources": [
            {
                "title": "UC Davis IPM - Grape Powdery Mildew Management",
                "url": "https://ipm.ucanr.edu/agriculture/grape/powdery-mildew/",
                "publisher": "UC Davis Agriculture"
            }
        ],
        "reviewed_at": "2026-10-24",
        "attribution": "Agricultural Research & Extension Plant Pathology Database"
    },
    {
        "slug": "grape-black-rot",
        "plant": "Grape",
        "condition": "Black Rot (Guignardia bidwellii)",
        "scientific_name": "Vitis vinifera",
        "class_ids": ["Grape___Black_rot"],
        "severity": "High",
        "symptoms": [
            "Small, circular reddish-brown leaf spots with distinct dark brown margins.",
            "Tiny black fruiting bodies (pycnidia) form in a ring inside each leaf lesion.",
            "Infected fruit shrivels into hard, black, mummified berries within days."
        ],
        "care": [
            "Remove and destroy all mummified berries and infected leaf debris from vines and ground.",
            "Apply preventative organic copper or sulfur sprays beginning at early bud break.",
            "Prune grapevines annually during dormancy to eliminate infected canes and cankers."
        ],
        "prevention": [
            "Train vines on high trellis systems to improve air movement and reduce drying time.",
            "Plant vines in well-drained soil with full, unobstructed south-facing sun exposure.",
            "Keep the vineyard floor clean and clear of weeds that trap ground moisture."
        ],
        "sources": [
            {
                "title": "Cornell University - Grape Black Rot Disease Guide",
                "url": "https://ecommons.cornell.edu/handle/1813/43094",
                "publisher": "Cornell Extension"
            }
        ],
        "reviewed_at": "2026-10-24",
        "attribution": "Agricultural Research & Extension Plant Pathology Database"
    }
]

def main():
    with open(CATALOG_PATH, "w", encoding="utf-8") as f:
        json.dump(CATALOG_DATA, f, indent=2)
    print(f"Successfully updated {CATALOG_PATH} with {len(CATALOG_DATA)} comprehensive disease entries.")

if __name__ == "__main__":
    main()
