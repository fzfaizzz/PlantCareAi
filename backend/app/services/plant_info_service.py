import json
from pathlib import Path


class PlantInfoService:
    def __init__(self):
        path = Path(__file__).resolve().parents[1] / "data" / "plant_diseases.json"
        self.entries = json.loads(path.read_text(encoding="utf-8"))
        self.by_class = {class_id: entry for entry in self.entries for class_id in entry["class_ids"]}

    def get_class(self, class_id):
        return self.by_class.get(class_id)

    def list(self, labels):
        supported = set(labels)
        return [{**entry, "model_supported": any(label in supported for label in entry["class_ids"])}
                for entry in self.entries]

    def get_slug(self, slug, labels):
        return next((item for item in self.list(labels) if item["slug"] == slug), None)
