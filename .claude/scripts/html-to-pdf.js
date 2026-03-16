#!/usr/bin/env node
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

  // Read the HTML content
  const html = fs.readFileSync(inputPath, 'utf8');

  console.log(`Converting: ${path.basename(inputPath)} -> ${path.basename(outputPath)}`);
  console.log(`  Format: ${format}, Margins: ${marginInches}in, Landscape: ${landscape}, Footer: ${!noFooter}`);

  // Launch headless Chrome
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  try {
    const page = await browser.newPage();

    // Resolve the base URL so relative paths (images, CSS) work correctly.
    // Using a file:// URL derived from the input HTML's directory.
    const baseUrl = 'file://' + path.dirname(inputPath) + '/';

    // Set the HTML content. waitUntil: 'networkidle0' ensures all resources
    // (images, fonts, external stylesheets) finish loading before we proceed.
    await page.setContent(html, {
      waitUntil: 'networkidle0',
      timeout: 30000
    });

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
        bottom: '1.25in',
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
