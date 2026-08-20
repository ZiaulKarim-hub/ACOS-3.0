#!/usr/bin/env node
// @ts-nocheck
// ACOS Loan Document Generator -- HTML to PDF Converter
// Uses Puppeteer (headless Chrome) for full CSS Paged Media support
//
// Usage: node html-to-pdf.js <input.html> <output.pdf> [options]
// Options:
//   --format letter|a4    Page format (default: letter)
//   --margin <inches>     All margins in inches (default: 1)
//   --no-footer           Disable page number footer
//   --landscape           Landscape orientation

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');
const { pathToFileURL } = require('url');

function parseArgs(argv) {
  const args = argv.slice(2);

  if (args.length < 2 || args[0] === '--help' || args[0] === '-h') {
    console.error(
      'Usage: node html-to-pdf.js <input.html> <output.pdf> [options]\n' +
      '\n' +
      'Options:\n' +
      '  --format letter|a4    Page format (default: letter)\n' +
      '  --margin <inches>     All margins in inches (default: 1)\n' +
      '  --no-footer           Disable page number footer\n' +
      '  --landscape           Landscape orientation\n' +
      '  --help, -h            Show this help message'
    );
    process.exit(args[0] === '--help' || args[0] === '-h' ? 0 : 1);
  }

  const inputPath = path.resolve(args[0]);
  const outputPath = path.resolve(args[1]);

  // Parse optional flags from remaining arguments
  const optArgs = args.slice(2);
  let format = 'letter';
  let marginInches = 1;
  let noFooter = false;
  let landscape = false;

  for (let i = 0; i < optArgs.length; i++) {
    switch (optArgs[i]) {
      case '--format':
        i++;
        if (!optArgs[i] || !['letter', 'a4'].includes(optArgs[i].toLowerCase())) {
          console.error('Error: --format must be "letter" or "a4"');
          process.exit(1);
        }
        format = optArgs[i].toLowerCase();
        break;
      case '--margin':
        i++;
        if (!optArgs[i] || isNaN(parseFloat(optArgs[i]))) {
          console.error('Error: --margin must be a number (inches)');
          process.exit(1);
        }
        marginInches = parseFloat(optArgs[i]);
        break;
      case '--no-footer':
        noFooter = true;
        break;
      case '--landscape':
        landscape = true;
        break;
      default:
        console.error(`Error: Unknown option "${optArgs[i]}"`);
        process.exit(1);
    }
  }

  return { inputPath, outputPath, format, marginInches, noFooter, landscape };
}

async function convertHtmlToPdf(options) {
  const { inputPath, outputPath, format, marginInches, noFooter, landscape } = options;

  // Validate input file exists
  if (!fs.existsSync(inputPath)) {
    console.error(`Error: Input file not found: ${inputPath}`);
    process.exit(1);
  }

  // Ensure output directory exists
  const outputDir = path.dirname(outputPath);
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  console.log(`Converting: ${path.basename(inputPath)} -> ${path.basename(outputPath)}`);
  console.log(`  Format: ${format}, Margins: ${marginInches}in, Landscape: ${landscape}, Footer: ${!noFooter}`);

  // Launch headless Chrome
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--allow-file-access-from-files']
  });

  try {
    const page = await browser.newPage();

    // page.goto() with a file:// URL sets the document origin to the file's
    // directory, so relative paths and <base href> resolve correctly. The
    // previous setContent() path left origin at about:blank and silently
    // dropped all image / font loads.
    // Prefer full network-idle, but degrade gracefully: a page with live
    // polling / analytics may never reach idle, and a hard reject here would
    // fail the whole conversion. Fall back to a DOM/load wait so a hung
    // resource doesn't sink an otherwise-renderable page.
    try {
      await page.goto(pathToFileURL(inputPath).href, {
        waitUntil: 'networkidle0',
        timeout: 60000
      });
    } catch (gotoErr) {
      // networkidle0 may never settle on pages with live polling/analytics;
      // degrade to a 'load' wait. But only swallow a fallback failure if the
      // page actually navigated — otherwise rethrow so main()'s .catch sets a
      // non-zero exit instead of rendering a blank/garbage PDF with exit 0.
      try {
        await page.goto(pathToFileURL(inputPath).href, {
          waitUntil: 'load',
          timeout: 60000
        });
      } catch (fallbackErr) {
        if (page.url() === 'about:blank') {
          throw fallbackErr;
        }
        // Page navigated despite the wait condition failing — proceed.
      }
    }

    // Strip loading="lazy" so off-screen images actually load. In headless
    // Chromium the IntersectionObserver behind native lazy-loading never fires
    // for images below the fold, so they render blank in the PDF. Removing the
    // attribute forces eager loading; we then wait for every <img> to settle.
    await page.evaluate(() => {
      document.querySelectorAll('img[loading]').forEach(i => i.removeAttribute('loading'));
    });

    // Wait for fonts and all (now eager) images to finish loading/decoding
    // before generating the PDF, so nothing renders blank.
    await page.evaluate(async () => {
      await document.fonts.ready;
      const imgs = Array.from(document.querySelectorAll('img'));
      await Promise.all(imgs.map(img => {
        if (img.complete && img.naturalWidth > 0) {
          return img.decode().catch(() => {});
        }
        return new Promise(resolve => {
          img.addEventListener('load', resolve, { once: true });
          img.addEventListener('error', resolve, { once: true });
        });
      }));
    });

    // Re-settle the network now that lazy images were forced to load
    await page.waitForNetworkIdle({ idleTime: 500, timeout: 30000 }).catch(() => {});

    // Brief pause for any deferred CSS rendering or font application
    await new Promise(resolve => setTimeout(resolve, 500));

    // Build PDF options
    const pdfOptions = {
      path: outputPath,
      format: format === 'a4' ? 'A4' : 'Letter',
      printBackground: true,
      landscape: landscape,
      margin: {
        top: `${marginInches}in`,
        right: `${marginInches}in`,
        bottom: noFooter ? `${marginInches}in` : '1.25in',
        left: `${marginInches}in`
      }
    };

    // Page number footer (unless --no-footer)
    if (!noFooter) {
      pdfOptions.displayHeaderFooter = true;
      // Empty header -- required when displayHeaderFooter is true
      pdfOptions.headerTemplate = '<div></div>';
      // Centered page numbers in small gray text
      pdfOptions.footerTemplate = [
        '<div style="',
        'font-size: 8pt;',
        'color: #999999;',
        'text-align: center;',
        'width: 100%;',
        'padding-top: 5px;',
        '">',
        'Page <span class="pageNumber"></span> of <span class="totalPages"></span>',
        '</div>'
      ].join(' ');
    }

    // Generate the PDF
    await page.pdf(pdfOptions);

    // Report results
    const stats = fs.statSync(outputPath);
    const sizeKB = (stats.size / 1024).toFixed(1);
    console.log(`PDF generated: ${outputPath} (${sizeKB} KB)`);

    return outputPath;

  } finally {
    await browser.close();
  }
}

// Main entry point
async function main() {
  const options = parseArgs(process.argv);
  await convertHtmlToPdf(options);
}

main().catch(err => {
  console.error(`PDF conversion failed: ${err.message}`);
  process.exit(1);
});
