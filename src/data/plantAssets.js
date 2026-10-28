const path = (name) => `/assets/plants/${name}.webp`;
export const plantAssets = Object.fromEntries([
  'tomato-healthy', 'tomato-early-blight', 'potato-late-blight', 'apple-scab', 'corn-common-rust', 'grape-powdery-mildew', 'healthy-dew-leaf',
  'tomato-healthy-library', 'tomato-early-blight-library', 'tomato-leaf-spot-library', 'potato-healthy-library', 'potato-late-blight-library', 'apple-scab-library', 'apple-black-rot-library', 'corn-healthy-library', 'corn-common-rust-library', 'grape-powdery-mildew-library',
  'reference-leaf-upper-left', 'reference-leaf-upper-right', 'reference-detect-hero', 'reference-about-hero', 'reference-about-hero-wide', 'reference-dataset-leaf', 'reference-avatars', 'home-leaf-left', 'home-leaf-right', 'home-foliage-bottom-left', 'home-foliage-bottom-right', 'home-botanical-background', 'sample-leaf-healthy', 'sample-leaf-spotted', 'sample-leaf-closeup', 'detect-preview-botanical', 'about-botanical-hero', 'about-foliage-decoration', 'dataset-botanical-image',
].map(name => [name, path(name)]));
export default plantAssets;



