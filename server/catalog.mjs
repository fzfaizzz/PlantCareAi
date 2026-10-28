import { readFileSync } from 'node:fs';

const entries = JSON.parse(readFileSync(new URL('./catalog.json', import.meta.url), 'utf8'));
const normalize = value => String(value || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
const plantNames = new Map([
  ['corn maize', 'corn'], ['maize', 'corn'], ['sweet corn', 'corn'],
  ['bell pepper', 'pepper'], ['tomato plant', 'tomato'], ['potato plant', 'potato'],
  ['apple tree', 'apple'], ['grapevine', 'grape'], ['grape vine', 'grape'],
]);
function plantName(value) { const name = normalize(value); return plantNames.get(name) || name; }

export const generalReference = {
  title: "What's wrong with my plant?",
  url: 'https://apps.extension.umn.edu/garden/diagnose/plant/',
  publisher: 'University of Minnesota Extension',
  attribution: 'General plant-problem assessment guidance; not a disease-specific treatment recommendation.',
};

export function listPlants() {
  return entries.map(entry => ({
    ...entry,
    plant_village_class: entry.class_ids[0] || null,
    model_supported: false,
    mapping_type: 'educational_catalog_only',
  }));
}

export function findPlant(slug) { return listPlants().find(entry => entry.slug === slug) || null; }

export function matchCatalog(plant, condition) {
  if (!plant || !condition) return null;
  return entries.find(entry => plantName(entry.plant) === plantName(plant) && normalize(entry.condition) === normalize(condition)) || null;
}

export function assembleResult(assessment, image, { requestId, model, timings }) {
  const reasons = [];
  const warnings = [
    'Plant identity and condition are Gemini image-based hypotheses, not a confirmed diagnosis.',
    'PlantVillage identifiers are educational catalog mappings; no TensorFlow classifier or dataset lookup runs here.',
    ...image.qualityWarnings,
    ...assessment.limitations.map(text => 'Image assessment limitation: ' + text),
  ];
  const unsupported = assessment.contains_leaf === 'no';
  if (assessment.contains_leaf === 'uncertain') reasons.push('A visible leaf could not be established.');
  if (assessment.image_quality !== 'usable') reasons.push('Image quality limits the assessment.');
  if (!assessment.plant) reasons.push('Plant identity could not be assessed.');
  if (!assessment.possible_condition || /^(unknown|uncertain|none|not sure)$/i.test(assessment.possible_condition)) {
    reasons.push('A possible condition could not be assessed.');
  }
  if (image.qualityWarnings.length) reasons.push('The uploaded photo has limited visual detail.');
  const entry = unsupported ? null : matchCatalog(assessment.plant?.common_name, assessment.possible_condition);
  if (!unsupported && !entry) {
    reasons.push('There is no exact plant-and-condition match in the reviewed care catalog.');
    warnings.push('No condition-specific care is available for this hypothesis; consult the general assessment reference.');
  }
  if (assessment.possible_condition && /healthy/i.test(assessment.possible_condition)) {
    warnings.push('Healthy-looking leaves do not rule out hidden disease, pests, or nutrient issues.');
  }
  const status = unsupported ? 'unsupported_image' : reasons.length ? 'uncertain' : 'success';
  return {
    schema_version: '2.0',
    request_id: requestId,
    status,
    plant: unsupported ? null : assessment.plant?.common_name || null,
    plant_scientific_name: unsupported ? null : assessment.plant?.scientific_name || null,
    condition: unsupported ? null : assessment.possible_condition,
    confidence: null,
    general_guidance: !unsupported && assessment.contains_leaf === 'yes' && assessment.image_quality === 'usable' && !entry ? [
      'Compare both sides of the leaf and nearby plants for similar changes.',
      'Record how symptoms change and consult a local plant specialist before treatment.',
    ] : [],
    general_guidance_source: !unsupported && assessment.contains_leaf === 'yes' && assessment.image_quality === 'usable' && !entry ? generalReference : null,
    provider: { name: 'gemini', model },
    observations: assessment.visible_symptoms,
    symptoms: assessment.visible_symptoms,
    care: unsupported ? [] : entry?.care || [],
    prevention: unsupported ? [] : entry?.prevention || [],
    uncertainty: unsupported ? 'The image does not show a usable leaf subject.' :
      reasons.join(' ') || 'A tentative visual assessment matched an educational care entry; it is not a definitive diagnosis.',
    explanation: unsupported ? 'Choose a clear photograph of a leaf for plant-health interpretation.' :
      'Gemini supplied the visible observations and tentative identity. ' +
      (entry ? 'Care information comes from the matched reviewed catalog entry.' : 'There is no reviewed care match for this hypothesis; the general assessment reference may help.'),
    warnings,
    sources: unsupported ? [] : entry?.sources || [generalReference],
    catalog: {
      matched: Boolean(entry), slug: entry?.slug || null,
      plant_village_class: entry?.class_ids[0] || null,
      attribution: entry ? entry.attribution : 'General plant-care guidance; no exact reviewed condition match.',
    },
    assessment: {
      contains_leaf: assessment.contains_leaf,
      image_quality: assessment.image_quality,
      limitations: assessment.limitations,
    },
    timings_ms: timings,
  };
}
