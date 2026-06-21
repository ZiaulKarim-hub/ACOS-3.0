---
name: acos-file-converter
description: |
  Universal document converter — converts any file type to any other format without
  quality loss. Interactive wizard for format selection and file path. Supports documents
  (PDF, DOCX, HTML, MD, TXT, RTF, EPUB, ODT), spreadsheets (XLSX, CSV, ODS, TSV),
  presentations (PPTX, ODP), images (PNG, JPG, SVG, TIFF, WEBP, BMP), and data formats
  (JSON, YAML, XML, TOML). Warns when lossless conversion is impossible. Use when the
  user wants to convert a file, change format, or transform documents.
disable-model-invocation: true
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
argument-hint: "[source-file] [--to format] [--output path]"
---

# ACOS File Converter

## Purpose

Converts any document, spreadsheet, presentation, image, or data file to any other
supported format with maximum quality preservation. When lossless conversion is impossible,
warns the user about what will be lost before proceeding. Includes post-conversion
validation to verify output integrity.

## When to Use

Invoke `/acos-file-converter` when:
- The user wants to convert a file from one format to another
- The user says "convert this PDF to Word" or "turn this XLSX into CSV"
- Any document format transformation is needed
- The user needs to change file format without losing content or formatting

## Supported Formats

### Documents
| Format | Extensions | Read | Write | Primary Tool |
|--------|-----------|------|-------|-------------|
| PDF | .pdf | Yes | Yes | Puppeteer (from HTML), LibreOffice, WeasyPrint |
| Word | .docx | Yes | Yes | python-docx, pandoc, LibreOffice |
| HTML | .html, .htm | Yes | Yes | Native (Read tool), pandoc |
| Markdown | .md | Yes | Yes | Native (Read tool), pandoc |
| Plain Text | .txt | Yes | Yes | Native (Read/Write tools) |
| Rich Text | .rtf | Yes | Yes | pandoc, LibreOffice, textutil (macOS) |
| EPUB | .epub | Yes | Yes | pandoc |
| OpenDocument | .odt | Yes | Yes | pandoc, LibreOffice |

### Spreadsheets
| Format | Extensions | Read | Write | Primary Tool |
|--------|-----------|------|-------|-------------|
| Excel | .xlsx, .xls | Yes | Yes | openpyxl (xlsx), LibreOffice (xls) |
| CSV | .csv | Yes | Yes | Python csv module |
| OpenDocument | .ods | Yes | Yes | LibreOffice |
| TSV | .tsv | Yes | Yes | Python csv module (tab delimiter) |

### Presentations
| Format | Extensions | Read | Write | Primary Tool |
|--------|-----------|------|-------|-------------|
| PowerPoint | .pptx | Yes | Yes | python-pptx, LibreOffice |
| OpenDocument | .odp | Yes | Yes | LibreOffice |
| PDF | .pdf | — | Yes | LibreOffice (from PPTX/ODP) |

### Images
| Format | Extensions | Read | Write | Primary Tool |
|--------|-----------|------|-------|-------------|
| PNG | .png | Yes | Yes | Pillow |
| JPEG | .jpg, .jpeg | Yes | Yes | Pillow |
| SVG | .svg | Yes | Yes | Pillow (raster), Inkscape (vector) |
| TIFF | .tiff, .tif | Yes | Yes | Pillow |
| WebP | .webp | Yes | Yes | Pillow |
| BMP | .bmp | Yes | Yes | Pillow |

### Data Formats
| Format | Extensions | Read | Write | Primary Tool |
|--------|-----------|------|-------|-------------|
| JSON | .json | Yes | Yes | Python json module |
| YAML | .yaml, .yml | Yes | Yes | Python PyYAML |
| XML | .xml | Yes | Yes | Python xml.etree |
| TOML | .toml | Yes | Yes | Python tomllib/tomli |
| CSV | .csv | Yes | Yes | Python csv module |

## Quality Loss Matrix

Before converting, consult this matrix. If the conversion is LOSSY, warn the user.

### Lossless Conversions (no quality loss)
- MD ↔ HTML ↔ TXT (text content preserved, formatting may simplify)
- JSON ↔ YAML ↔ TOML (data structure preserved exactly)
- PNG → BMP, TIFF (lossless image formats)
- XLSX → ODS (via LibreOffice, formulas preserved)
- DOCX → ODT (via LibreOffice/pandoc)
- CSV ↔ TSV (delimiter change only)

### Lossy Conversions (warn user)
- **XLSX → CSV**: Loses formulas (values only), multiple sheets, formatting, charts
- **PDF → DOCX**: Font substitution, layout drift, table misalignment possible
- **PDF → TXT/MD**: Loses all formatting, images, tables
- **DOCX → TXT**: Loses all formatting, images, tables
- **PPTX → PDF**: Animations lost, speaker notes may be excluded
- **JPG → PNG**: No quality improvement (already compressed with loss)
- **SVG → PNG/JPG**: Vector-to-raster = resolution-dependent (warn about DPI)

### Impossible/Not Recommended
- **Scanned PDF → any text format**: Requires OCR (not supported — warn and halt)
- **CSV → XLSX with formulas**: CSV has no formula information to restore
- **TXT → DOCX with styling**: No style information in source
- **Raster → SVG**: Produces embedded raster, not true vector (warn)

## Restricted Boundaries

**NEVER read or write to:**
- `review-rules/` — ACOS restricted (Independence Wall)
- `.claude/agents/` — Agent definitions (human-editable only)
- `.acos/config/oracle.yaml` — Oracle configuration

**Path validation:** All file paths (source and output) must be validated:
- Resolve to absolute path
- Reject paths with `..` traversal
- Reject system directories (`/etc/`, `/usr/`, `/var/`, `~/.ssh/`)
- Reject symlinks pointing outside user's home directory

## Skill Protocol

### Phase 0: Interactive Format Wizard

**If `$ARGUMENTS` are provided**, parse them:
- First positional arg = source file path
- `--to <format>` = target format (must be one of the supported format names: pdf, docx, html, md, txt, rtf, epub, odt, xlsx, csv, ods, tsv, pptx, odp, png, jpg, svg, tiff, webp, bmp, json, yaml, xml, toml). Reject unrecognized formats with an error listing valid options.
- `--output <path>` = output file path (optional, defaults to same directory as source)

**File size check:** Before proceeding, check the source file size. If >500MB, warn:
"This file is {size}. Large files may take significant time and memory. Proceed? [Y/n]"
If >2GB, warn: "Files over 2GB may exceed available memory. Consider splitting first."

**If no arguments or incomplete**, run the interactive wizard:

**Step 1: Source File**
```
What file would you like to convert?
  [Provide the full path to the file]
```

Validate: file exists, is readable, detect format from extension. If the file has no
extension or an unrecognized extension, attempt to detect format from content (magic bytes
for images, XML declaration for XML, etc.).

**Step 2: Target Format**
```
Convert from: [detected-format] ({filename})

What format would you like to convert to?

  DOCUMENTS          SPREADSHEETS      PRESENTATIONS     IMAGES          DATA
  [1] PDF            [6] XLSX          [10] PPTX         [12] PNG        [17] JSON
  [2] DOCX           [7] CSV           [11] ODP          [13] JPG        [18] YAML
  [3] HTML           [8] ODS           [    ] PDF*       [14] SVG        [19] XML
  [4] Markdown       [9] TSV                             [15] TIFF       [20] TOML
  [5] TXT                                                [16] WEBP
  [  ] RTF
  [  ] EPUB
  [  ] ODT

  * Presentations can be converted to PDF via the Documents column

Select target format [1-20]:
```

Only show formats that are valid targets for the detected source format. Gray out or
exclude impossible conversions.

**Step 3: Quality Warning (if lossy)**

Consult the Quality Loss Matrix. If the conversion path is lossy:
```
WARNING: Converting {source_format} to {target_format} may result in:
  - [specific losses for this conversion path]

Proceed anyway? [Y/n]
```

If the conversion is IMPOSSIBLE (e.g., scanned PDF to text), explain why and suggest
alternatives (e.g., "This PDF appears to be scanned images. Text extraction requires
OCR which is not supported. Consider using an OCR tool first, then convert the result.").

**Step 4: Output Location**
```
Output location:
  [1] Same directory as source (default)
  [2] Desktop
  [3] Custom path

Select [1-3]:
```

Default filename: `{original_name}.{target_extension}`
If file already exists at target, ask: "File already exists. Overwrite? [Y/n]"

**Step 5: Confirmation**
```
Conversion Summary:
  Source:  {source_path} ({source_format}, {file_size})
  Target:  {target_path} ({target_format})
  Tool:    {conversion_tool}
  Quality: {Lossless | Lossy — [what's lost]}

Proceed? [Y/n]
```

### Phase 1: Dependency Check

Before converting, verify the required tool is available:

| Tool | Check Command | Install Hint |
|------|--------------|-------------|
| pandoc | `pandoc --version` | `brew install pandoc` |
| LibreOffice | `soffice --version` | `brew install --cask libreoffice` |
| Puppeteer | `node -e "require('puppeteer')"` | `npm install puppeteer` |
| openpyxl | `python3 -c "import openpyxl"` | `pip3 install openpyxl` |
| python-docx | `python3 -c "import docx"` | `pip3 install python-docx` |
| python-pptx | `python3 -c "import pptx"` | `pip3 install python-pptx` |
| Pillow | `python3 -c "from PIL import Image"` | `pip3 install Pillow` |
| PyYAML | `python3 -c "import yaml"` | `pip3 install PyYAML` |
| WeasyPrint | `python3 -c "import weasyprint"` | `pip3 install weasyprint` |
| textutil | `which textutil` | Built-in on macOS |

If a required tool is missing:
```
Required tool not found: {tool}
Install with: {install_command}

Would you like me to install it? [Y/n]
```

Only install with explicit user confirmation. Never install silently.

### Phase 2: Execute Conversion

Select the conversion strategy based on the source→target pair.

**CRITICAL — Shell Safety:** When constructing shell commands, ALWAYS use single quotes
around file paths to prevent shell metacharacter injection. For filenames containing
single quotes, use `printf '%q'` to escape. Never use double quotes alone for paths
with user-supplied filenames. Example: `soffice --headless --convert-to pdf '/path/to/file.docx'`

#### Document Conversions
| Path | Strategy |
|------|----------|
| DOCX → PDF | LibreOffice: `soffice --headless --convert-to pdf "{file}"` |
| DOCX → HTML | pandoc: `pandoc -f docx -t html -o "{out}" "{file}"` |
| DOCX → MD | pandoc: `pandoc -f docx -t markdown -o "{out}" "{file}"` |
| DOCX → TXT | pandoc: `pandoc -f docx -t plain -o "{out}" "{file}"` |
| DOCX → RTF | LibreOffice or pandoc |
| DOCX → ODT | pandoc: `pandoc -f docx -t odt -o "{out}" "{file}"` |
| DOCX → EPUB | pandoc: `pandoc -f docx -t epub -o "{out}" "{file}"` |
| HTML → PDF | Puppeteer (best quality) or WeasyPrint (no Node needed) |
| HTML → DOCX | pandoc with reference doc for styling |
| HTML → MD | pandoc: `pandoc -f html -t markdown -o "{out}" "{file}"` |
| MD → PDF | pandoc → HTML → Puppeteer (best) or pandoc direct |
| MD → DOCX | pandoc: `pandoc -f markdown -t docx -o "{out}" "{file}"` |
| MD → HTML | pandoc: `pandoc -f markdown -t html -o "{out}" "{file}"` |
| PDF → DOCX | LibreOffice: `soffice --headless --convert-to docx "{file}"` (warn: lossy) |
| PDF → TXT | Python: `pypdf` or Read tool extraction |
| PDF → HTML | LibreOffice or poppler's `pdftohtml` |
| TXT → PDF | Wrap in HTML with basic styling → Puppeteer |
| TXT → DOCX | pandoc: `pandoc -f plain -t docx -o "{out}" "{file}"` |
| RTF → DOCX | pandoc or textutil (macOS): `textutil -convert docx "{file}"` |
| ODT → DOCX | pandoc or LibreOffice |

#### Spreadsheet Conversions
| Path | Strategy |
|------|----------|
| XLSX → CSV | Python: openpyxl read → csv write (active sheet only; warn about multi-sheet loss) |
| XLSX → ODS | LibreOffice: `soffice --headless --convert-to ods "{file}"` |
| XLSX → TSV | Python: openpyxl read → csv write with tab delimiter |
| XLSX → PDF | LibreOffice: `soffice --headless --convert-to pdf "{file}"` |
| CSV → XLSX | Python: openpyxl — create workbook, write rows, auto-size columns |
| CSV → JSON | Python: csv.DictReader → json.dump |
| ODS → XLSX | LibreOffice: `soffice --headless --convert-to xlsx "{file}"` |

#### Presentation Conversions
| Path | Strategy |
|------|----------|
| PPTX → PDF | LibreOffice: `soffice --headless --convert-to pdf "{file}"` |
| PPTX → ODP | LibreOffice |
| ODP → PPTX | LibreOffice |
| ODP → PDF | LibreOffice |

#### Image Conversions
| Path | Strategy |
|------|----------|
| Any raster → Any raster | Python Pillow: `Image.open(src).save(dst)` with format-specific options |
| PNG → JPG | Pillow with quality=95, handle alpha→white background |
| JPG → PNG | Pillow (lossless from lossy source — warn no quality recovery) |
| SVG → PNG/JPG | Pillow (rasterize) or Inkscape CLI for better quality |
| Any → SVG | Warn: produces embedded raster, not true vector conversion |

**Image quality options:** For lossy formats (JPG, WebP), use quality=95 by default.
For PNG, use maximum compression. Preserve original DPI/resolution.

#### Data Format Conversions
| Path | Strategy |
|------|----------|
| JSON → YAML | Python: `json.load()` → `yaml.dump(default_flow_style=False)` |
| YAML → JSON | Python: `yaml.safe_load()` → `json.dump(indent=2)` |
| JSON → XML | Python: dict→XML with `xml.etree.ElementTree` |
| JSON → TOML | Python: `json.load()` → `tomli_w.dumps()` (or manual) |
| XML → JSON | Python: `xml.etree` → recursive dict → `json.dump` |
| CSV → JSON | Python: `csv.DictReader` → `json.dump` |
| YAML → TOML | Python: YAML→dict→TOML |

### Phase 3: Post-Conversion Validation

After conversion completes, verify the output:

1. **File exists check**: Verify the output file was created
2. **File size check**: Output should be >0 bytes. If 0 bytes, the conversion failed silently.
3. **Format-specific validation**:
   - **PDF**: Verify it's a valid PDF (starts with `%PDF-`)
   - **DOCX/XLSX/PPTX**: Verify it's a valid ZIP (these are ZIP archives)
   - **JSON**: Parse and verify valid JSON
   - **YAML**: Parse and verify valid YAML
   - **XML**: Parse and verify well-formed XML
   - **Images**: Open with Pillow, verify dimensions > 0
   - **CSV/TSV**: Read first line, verify delimiter consistency
4. **Content spot-check** (for text-based formats):
   - For small files (<100 lines): read the entire output and compare against source
   - For medium files (100-1000 lines): read first 50 lines, middle 20 lines, and last 20 lines
   - For large files (>1000 lines): read first 50, a random middle sample of 30, and last 20
   - Compare key content markers against source (title, first paragraph, key numbers, last paragraph)
   - If source had N pages/rows, verify output has comparable content volume
   - For numerical content: spot-check at least 5 specific values across different sections
5. **Scanned PDF detection** (for PDF sources):
   - Read the PDF with the Read tool
   - If the extracted text is empty or <10 characters per page, the PDF is likely scanned
   - Warn: "This PDF appears to contain scanned images rather than text. The conversion
     may produce empty or unusable output. Consider using OCR first."

### Phase 4: Delivery

1. Report the conversion result:
```
Conversion complete!
  Source:  {source_path} ({source_size})
  Output:  {output_path} ({output_size})
  Format:  {source_format} → {target_format}
  Quality: {Lossless | Lossy}
  Tool:    {tool_used}
```

2. If the output is a text-readable format, offer to show a preview:
```
Would you like to preview the output? [Y/n]
```

3. Clean up any temporary/intermediate files created during conversion.

## Data Integrity Rules

1. **EXACT CONTENT PRESERVATION**: The converter must not add, remove, or modify content.
   Numbers must appear exactly as in the source. Text must be character-identical.
2. **NO FABRICATION**: Never generate content that wasn't in the source document.
3. **TRANSPARENCY**: If quality loss occurs, document exactly what was lost in the
   conversion report.
4. **METADATA PRESERVATION**: Where the target format supports it, preserve document
   metadata (author, title, creation date, etc.).
5. **ENCODING SAFETY**: Always use UTF-8 encoding for text-based outputs. If the source
   uses a different encoding, detect and transcode correctly.

## Error Handling

| Error | Action |
|-------|--------|
| Source file not found | Report error, re-prompt for path |
| Source format unrecognized | List supported formats, ask user to specify |
| Required tool not installed | Show install command, offer to install |
| Conversion tool crashes | Report the error output, suggest alternative tool |
| Output file is 0 bytes | Report failure, try alternative conversion path |
| Output validation fails | Report what failed, offer to retry with different tool |
| Scanned PDF detected | Warn user, suggest OCR, do not proceed silently |
| Permission denied on output path | Suggest alternative path (Desktop) |
| Disk space insufficient | Report error before conversion |

## Quality Checklist

- [ ] Source file exists and is readable
- [ ] Target format is valid for the source format
- [ ] User warned about lossy conversions before proceeding
- [ ] Required conversion tool is available
- [ ] Output file exists and is non-zero bytes
- [ ] Output format validation passed
- [ ] Content spot-check passed
- [ ] No temporary files left behind
- [ ] Data integrity rules followed

## Output

- Converted file at the specified output path
- Conversion report (inline, not saved to file)
- Preview of output (if user requests)

---
*ACOS File Converter — Universal format conversion with zero tolerance for silent quality loss.*
