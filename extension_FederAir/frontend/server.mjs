import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PORT = Number(process.env.PORT || 5500);
const targets = {
  environment: process.env.ENVIRONMENT_URL || 'http://127.0.0.1:8001',
  hospital: process.env.HOSPITAL_URL || 'http://127.0.0.1:8002',
  analytics: process.env.ANALYTICS_URL || 'http://127.0.0.1:8003'
};
const mime = { '.html':'text/html; charset=utf-8', '.css':'text/css; charset=utf-8', '.js':'text/javascript; charset=utf-8', '.svg':'image/svg+xml', '.json':'application/json; charset=utf-8' };

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://${req.headers.host || 'localhost'}`);
  const match = url.pathname.match(/^\/proxy\/(environment|hospital|analytics)(\/.*)$/);
  if (match) {
    const [, node, route] = match;
    const target = `${targets[node]}${route}${url.search}`;
    try {
      const headers = { 'accept': req.headers.accept || 'application/json' };
      if (req.headers['content-type']) headers['content-type'] = req.headers['content-type'];
      if (req.headers['x-api-key']) headers['x-api-key'] = req.headers['x-api-key'];
      const chunks = [];
      for await (const chunk of req) chunks.push(chunk);
      const body = chunks.length ? Buffer.concat(chunks) : undefined;
      const upstream = await fetch(target, { method: req.method, headers, body, signal: AbortSignal.timeout(15000) });
      const data = Buffer.from(await upstream.arrayBuffer());
      res.writeHead(upstream.status, { 'content-type': upstream.headers.get('content-type') || 'application/json', 'cache-control':'no-store' });
      res.end(data);
    } catch (err) {
      res.writeHead(502, { 'content-type':'application/json; charset=utf-8' });
      res.end(JSON.stringify({ detail:`Impossible de joindre ${node === 'environment' ? 'Environment' : node === 'hospital' ? 'Hospital' : 'Intelligence'} : ${err.message}` }));
    }
    return;
  }
  let pathname = decodeURIComponent(url.pathname);
  if (pathname === '/') pathname = '/index.html';
  const file = path.resolve(__dirname, `.${pathname}`);
  if (!file.startsWith(__dirname + path.sep) && file !== path.join(__dirname, 'index.html')) {
    res.writeHead(403); res.end('Forbidden'); return;
  }
  fs.readFile(file, (err, data) => {
    if (err) { res.writeHead(404, {'content-type':'text/plain; charset=utf-8'}); res.end('Not found'); return; }
    res.writeHead(200, { 'content-type': mime[path.extname(file)] || 'application/octet-stream', 'cache-control':'no-store' });
    res.end(data);
  });
});
server.listen(PORT, '127.0.0.1', () => console.log(`\n  FederAir Health UI ready → http://127.0.0.1:${PORT}\n  Environment API → ${targets.environment}\n  Hospital API    → ${targets.hospital}\n  Intelligence API → ${targets.analytics}\n`));
