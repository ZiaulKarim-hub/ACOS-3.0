#!/usr/bin/env node
// render-pdf.mjs — Puppeteer tear-sheet render. Mimics v3 .build/render.mjs.
//
// Usage: node render-pdf.mjs --input <html> --output <pdf> [--timeout 120]

import puppeteer from 'puppeteer';
import { promises as fs } from 'fs';
import path from 'path';
import { pathToFileURL } from 'url';

function parseArgs(argv) {
  const args = argv.slice(2);
  const out = { timeout: 120 };
  for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
      case '--input':   out.input   = args[++i]; break;
      case '--output':  out.output  = args[++i]; break;
      case '--timeout': out.timeout = parseInt(args[++i], 10); break;
      case '-h': case '--help':
        console.log('Usage: render-pdf.mjs --input <html> --output <pdf> [--timeout 120]');
        process.exit(0);
      default:
        console.error(`Unknown arg: ${args[i]}`);
        process.exit(1);
    }
  }
  if (!out.input || !out.output) {
    console.error('Error: --input and --output required');
    process.exit(1);
  }
  return out;
}

async function render({ input, output, timeout }) {
  await fs.access(input);
  const absIn = path.resolve(input);
  const url = pathToFileURL(absIn).href;

  const browser = await puppeteer.launch({
    headless: 'new',
    args: [
      '--no-sandbox',
      '--disable-dev-shm-usage',
      // Without this, Chromium blocks `file://` subresource loads when the
      // HTML itself is loaded from a `file://` URL — each local file URL is
      // treated as a distinct origin for security. Symptom: backgrounds and
      // images silently fail to load, producing an image-less PDF even
      // though the HTML references 12 valid background-image rules. This
      // flag opts the local document into loading sibling local assets.
      '--allow-file-access-from-files',
    ],
  });
  try {
    const page = await browser.newPage();
    await page.emulateMediaType('print');
    await page.goto(url, { waitUntil: 'networkidle0', timeout: timeout * 1000 });
    await page.evaluate(async () => {
      if (document.fonts && document.fonts.ready) {
        await document.fonts.ready;
      }
    });
    // Tiny extra settle for image decoding
    await new Promise(r => setTimeout(r, 500));

    await page.pdf({
      path: output,
      format: 'Letter',
      printBackground: true,
      preferCSSPageSize: true,
      margin: { top: 0, right: 0, bottom: 0, left: 0 },
    });
    console.error(`Rendered ${output}`);
  } finally {
    await browser.close();
  }
}

const args = parseArgs(process.argv);
render(args).catch(err => {
  console.error('render-pdf.mjs failed:', err.message);
  process.exit(2);
});
