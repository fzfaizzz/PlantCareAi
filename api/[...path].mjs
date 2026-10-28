import { createVercelHandler } from '../server/index.mjs';

// A Node function keeps the SDK and secret key outside the Vite browser bundle.
export default createVercelHandler();
