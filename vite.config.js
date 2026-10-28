import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

function plantCareApi(env) {
 let handler;
 const middleware = async (request, response, next) => {
  if (!/^\/api(?:\/|\?|$)/.test(request.url || '')) return next();
  try {
   if (!handler) {
    const { createApiHandler } = await import('./server/index.mjs');
    handler = createApiHandler({ env });
   }
   await handler(request, response);
  } catch {
   if (!response.headersSent) {
    response.statusCode = 500;
    response.setHeader('Content-Type', 'application/json');
    response.end(JSON.stringify({ code: 'service_unavailable', message: 'The analysis service could not start. Check server configuration.' }));
   } else response.end();
  }
 };
 return { name: 'plantcare-server-api', configureServer(server) { server.middlewares.use(middleware); }, configurePreviewServer(server) { server.middlewares.use(middleware); } };
}

export default defineConfig(({ mode }) => {
 const env = loadEnv(mode, process.cwd(), '');
 return { plugins: [react(), plantCareApi(env)], server: { port: 5173, strictPort: true } };
});
