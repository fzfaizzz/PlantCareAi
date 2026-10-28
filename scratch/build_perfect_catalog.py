import json
from pathlib import Path

catalog = [
    {
        "slug": "tomato-healthy",
        "plant": "Tomato",
        "condition": "Healthy",
        "class_ids": ["Tomato___healthy"],
        "symptoms": [
            "No obvious disease-like markings in the reference class."
        ],
        "care": [
            "Check both sides of leaves for changes.",
            "Follow crop-specific watering, light, and soil guidance."
        ],
        "prevention": [
            "Monitor new growth regularly."
        ],
        "sources": [
            {
                "title": "Growing tomatoes in home gardens",
                "url": "https://extension.umn.edu/garden-and-home/yard-and-garden/gardening-in-minnesota/growing-tomatoes",
                "publisher": "University of Minnesota Extension"
            }
        ],
        "reviewed_at": "2026-10-23",
        "attribution": "Curated reference information; these symptoms are not observations of the uploaded photo."
    },
    {
        "slug": "tomato-early-blight",
        "plant": "Tomato",
        "condition": "Early Blight",
        "class_ids": ["Tomato___Early_blight"],
        "symptoms": [
            "Brown leaf spots can form concentric rings.",
            "Older affected leaves may yellow."
        ],
        "care": [
            "Keep irrigation off leaves where practical.",
            "Remove affected crop debris and consult local extension guidance."
        ],
        "prevention": [
            "Rotate growing locations and provide adequate spacing."
        ],
        "sources": [
            {
                "title": "Tomato leaf spot diseases",
                "url": "https://extension.umn.edu/garden-and-home/yard-and-garden/gardening-in-minnesota/yard-and-garden-problems/tomato-leaf-spot-diseases",
                "publisher": "University of Minnesota Extension"
            }
        ],
        "reviewed_at": "2026-10-23",
        "attribution": "Curated reference information; these symptoms are not observations of the uploaded photo."
    },
    {
        "slug": "tomato-late-blight",
        "plant": "Tomato",
        "condition": "Late Blight",
        "class_ids": ["Tomato___Late_blight"],
        "symptoms": [
            "Large, dark, water-soaked spots appear on leaves and stems.",
            "White fungal growth can appear on undersides of leaves in humid conditions."
        ],
        "care": [
            "Remove and destroy severely affected plants immediately.",
            "Avoid working with plants when foliage is wet."
        ],
        "prevention": [
            "Plant resistant tomato varieties.",
            "Ensure wide spacing between plants for good airflow."
        ],
        "sources": [
            {
                "title": "Tomato late blight",
                "url": "https://extension.umn.edu/garden-and-home/yard-and-garden/gardening-in-minnesota/yard-and-garden-problems/late-blight",
                "publisher": "University of Minnesota Extension"
            }
        ],
        "reviewed_at": "2026-10-23",
        "attribution": "Curated reference information; these symptoms are not observations of the uploaded photo."
    },
    {
        "slug": "potato-healthy",
        "plant": "Potato",
        "condition": "Healthy",
        "class_ids": ["Potato___healthy"],
        "symptoms": [
            "Uniform green leaf foliage without discoloration or lesions."
        ],
        "care": [
            "Maintain consistent soil moisture and adequate hilling.",
            "Monitor periodically for Colorado potato beetles."
        ],
        "prevention": [
            "Use certified disease-free seed potatoes."
        ],
        "sources": [
            {
                "title": "Growing potatoes in home gardens",
                "url": "https://extension.umn.edu/vegetables/growing-potatoes",
                "publisher": "University of Minnesota Extension"
            }
        ],
        "reviewed_at": "2026-10-23",
        "attribution": "Curated reference information; these symptoms are not observations of the uploaded photo."
    },
    {
        "slug": "potato-early-blight",
        "plant": "Potato",
        "condition": "Early Blight",
        "class_ids": ["Potato___Early_blight"],
        "symptoms": [
            "Small dark brown to black spots with characteristic concentric rings.",
            "Yellow halo surrounding the dark lesions on older lower foliage."
        ],
        "care": [
            "Prune infected lower foliage to reduce fungal spore count.",
            "Ensure balanced fertilization and avoid water stress."
        ],
        "prevention": [
            "Use certified disease-free seed tubers.",
            "Rotate potato fields with non-solanaceous crops on a 3-year cycle."
        ],
        "sources": [
            {
                "title": "Potato Early Blight Biology and Management",
                "url": "https://extension.umn.edu/potato-pest-management/early-blight-potatoes",
                "publisher": "University of Minnesota Extension"
            }
        ],
        "reviewed_at": "2026-10-24",
        "attribution": "Curated reference information; these symptoms are not observations of the uploaded photo."
    },
    {
        "slug": "potato-late-blight",
        "plant": "Potato",
        "condition": "Late Blight",
        "class_ids": ["Potato___Late_blight"],
        "symptoms": [
            "Water-soaked dark lesions spreading rapidly across leaf tips and margins.",
            "White fungal growth on leaf undersides in humid conditions."
        ],
        "care": [
            "Remove and bag infected plant material immediately.",
            "Apply protectant sprays when cool, moist weather threatens."
        ],
        "prevention": [
            "Plant certified clean seed potatoes.",
            "Eliminate all cull piles and volunteer plants."
        ],
        "sources": [
            {
                "title": "Late blight on potatoes and tomatoes",
                "url": "https://extension.umn.edu/potato-pest-management/late-blight-potatoes",
                "publisher": "University of Minnesota Extension"
            }
        ],
        "reviewed_at": "2026-10-23",
        "attribution": "Curated reference information; these symptoms are not observations of the uploaded photo."
    },
    {
        "slug": "apple-scab",
        "plant": "Apple",
        "condition": "Apple Scab",
        "class_ids": ["Apple___Apple_scab"],
        "symptoms": [
            "Olive-green to dark brown velvety spots on leaf surfaces.",
            "Leaves may become distorted, puckered, and drop prematurely."
        ],
        "care": [
            "Rake and destroy fallen leaves in autumn.",
            "Prune canopy branches to improve air circulation."
        ],
        "prevention": [
            "Plant resistant apple varieties like Honeycrisp or Liberty.",
            "Avoid overhead sprinkler irrigation."
        ],
        "sources": [
            {
                "title": "Apple scab",
                "url": "https://extension.umn.edu/fruit/apple-pest-management",
                "publisher": "University of Minnesota Extension"
            }
        ],
        "reviewed_at": "2026-10-23",
        "attribution": "Curated reference information; these symptoms are not observations of the uploaded photo."
    },
    {
        "slug": "apple-black-rot",
        "plant": "Apple",
        "condition": "Black Rot",
        "class_ids": ["Apple___Black_rot"],
        "symptoms": [
            "Circular purple spots on leaves that expand to brown frog-eye spots.",
            "Black rotting areas on fruit and cankers on branches."
        ],
        "care": [
            "Prune out dead wood and cankers during dormancy.",
            "Remove mummified apples from trees and orchard floor."
        ],
        "prevention": [
            "Maintain tree vigor through proper pruning and nutrition."
        ],
        "sources": [
            {
                "title": "Apple black rot",
                "url": "https://extension.umn.edu/fruit/apple-pest-management",
                "publisher": "University of Minnesota Extension"
            }
        ],
        "reviewed_at": "2026-10-23",
        "attribution": "Curated reference information; these symptoms are not observations of the uploaded photo."
    },
    {
        "slug": "corn-healthy",
        "plant": "Corn",
        "condition": "Healthy",
        "class_ids": ["Corn_(maize)___healthy"],
        "symptoms": [
            "Vibrant green leaf blades without pustules, stripes, or lesions."
        ],
        "care": [
            "Ensure regular irrigation during tasseling and silking.",
            "Provide balanced nitrogen and phosphorus feeding."
        ],
        "prevention": [
            "Plant adapted hybrids suited to regional climate."
        ],
        "sources": [
            {
                "title": "Corn production guides",
                "url": "https://extension.umn.edu/corn",
                "publisher": "University of Minnesota Extension"
            }
        ],
        "reviewed_at": "2026-10-23",
        "attribution": "Curated reference information; these symptoms are not observations of the uploaded photo."
    },
    {
        "slug": "corn-common-rust",
        "plant": "Corn",
        "condition": "Common Rust",
        "class_ids": ["Corn___Common_rust", "Corn_(maize)___Common_rust_"],
        "symptoms": [
            "Cinnamon-brown powdery pustules on both upper and lower leaf surfaces."
        ],
        "care": [
            "Monitor fields regularly during warm, humid conditions.",
            "Apply foliar fungicides early if lesions spread before silking."
        ],
        "prevention": [
            "Select rust-resistant hybrid varieties.",
            "Practice crop rotation with non-host crops."
        ],
        "sources": [
            {
                "title": "Common rust of corn",
                "url": "https://extension.umn.edu/corn-pest-management/corn-diseases",
                "publisher": "University of Minnesota Extension"
            }
        ],
        "reviewed_at": "2026-10-23",
        "attribution": "Curated reference information; these symptoms are not observations of the uploaded photo."
    },
    {
        "slug": "grape-powdery-mildew",
        "plant": "Grape",
        "condition": "Powdery Mildew",
        "class_ids": [],
        "symptoms": [
            "White or gray powdery coating on leaves, shoots, and young berries."
        ],
        "care": [
            "Prune dense canopies to maximize sun exposure and air movement.",
            "Apply approved sulfur or bio-fungicide sprays early in the season."
        ],
        "prevention": [
            "Plant in full sun with rows oriented to prevailing winds."
        ],
        "sources": [
            {
                "title": "Powdery mildew on grapes",
                "url": "https://extension.umn.edu/fruit/growing-grapes-home-garden",
                "publisher": "University of Minnesota Extension"
            }
        ],
        "reviewed_at": "2026-10-23",
        "attribution": "Curated reference information; these symptoms are not observations of the uploaded photo."
    },
    {
        "slug": "grape-black-rot",
        "plant": "Grape",
        "condition": "Black Rot",
        "class_ids": ["Grape___Black_rot"],
        "symptoms": [
            "Reddish-brown circular leaf spots with tiny black fruiting bodies.",
            "Berries shrivel into hard, black, wrinkled mummies."
        ],
        "care": [
            "Remove and destroy mummified fruit clusters.",
            "Maintain good weed management under grape trellises."
        ],
        "prevention": [
            "Apply preventative fungicides from early shoot growth through veraison."
        ],
        "sources": [
            {
                "title": "Black rot of grape",
                "url": "https://extension.umn.edu/fruit/growing-grapes-home-garden",
                "publisher": "University of Minnesota Extension"
            }
        ],
        "reviewed_at": "2026-10-23",
        "attribution": "Curated reference information; these symptoms are not observations of the uploaded photo."
    }
]

p1 = Path("server/catalog.json")
p2 = Path("plantcare_streamlit/data/catalog.json")

p1.write_text(json.dumps(catalog, indent=2), encoding="utf-8")
p2.write_text(json.dumps(catalog, indent=2), encoding="utf-8")
print(f"Updated {p1} and {p2} with {len(catalog)} entries!")
