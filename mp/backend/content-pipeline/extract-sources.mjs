// Mechanical, deterministic source-file extraction. No LLM calls.
//
// Walks the included course folders (and selected textbooks) and pulls raw
// text out of .pptx / .pdf / .ipynb / .docx / .rmd / .html / .txt / .md files,
// writing one .txt dump per source file under backend/content-pipeline/extracted/<bucket>/...
// preserving the relative folder structure (so module/topic grouping survives
// for the later taxonomy + authoring passes).
//
// Run from frontend/: npm run extract
import { readFileSync, writeFileSync, mkdirSync, readdirSync, statSync } from 'node:fs';
import { join, relative, extname, basename, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { PDFParse } from 'pdf-parse';
import mammoth from 'mammoth';
import JSZip from 'jszip';
import { convert as htmlToText } from 'html-to-text';

/**
 * Root folder for private/local source material.
 *
 * The public repository must not assume a contributor has the original
 * authoring folders. Set MP_SOURCE_ROOT when running the private extraction
 * workflow, for example:
 *
 *   MP_SOURCE_ROOT="/path/to/approved/source-material" npm run extract
 */
const ROOT = process.env.MP_SOURCE_ROOT ?? '';
/** Configuration or lookup table for OUT_ROOT; keeping it named makes future tuning safer. */
const OUT_ROOT = fileURLToPath(new URL('./extracted/', import.meta.url));

// Bucket name -> source directory to walk. These paths are intentionally
// expressed relative to MP_SOURCE_ROOT so the public repo is portable.
const SOURCES = {
  'isa512': `${ROOT}/Classes /Fall 2025/ISA 512`,
  'isa514': `${ROOT}/Classes /Fall 2025/ISA 514`,
  'isa591': `${ROOT}/Classes /Fall 2025/ISA 591`,
  'isa634': `${ROOT}/Classes /Fall 2025/ISA 634`,
  'isa630': `${ROOT}/Classes /Spring 2026/ISA 630`,
  'isa632': `${ROOT}/Classes /Spring 2026/ISA 632`,
  'isa633': `${ROOT}/Classes /Spring 2026/ISA 633`,
  'its241': `${ROOT}/Undergrad/Gen Eds/Miami 2025 Summer /ITS 241`,
  'lit-d2l': `${ROOT}/Literature to Know/DB, BI, & Analytics/ML/d2l-en (1)/pytorch`,
  'lit-data-eng': `${ROOT}/Literature to Know/DB, BI, & Analytics`,
  'lit-ai': `${ROOT}/Literature to Know/AI`,
};

// Extra per-bucket directory-name skips, beyond SKIP_DIR_PATTERNS (e.g. to
// avoid re-walking a subfolder that already has its own dedicated bucket).
const EXTRA_SKIP = {
  'lit-data-eng': ['ml'],
};

// Directory name substrings (case-insensitive) to skip entirely.
const SKIP_DIR_PATTERNS = [
  'node_modules', '.git', '.ipynb_checkpoints', '.rproj.user', '__pycache__',
  'venv', '.venv', 'dist', 'build', 'target', 'zips', '.cache',
];

/** Configuration or lookup table for SUPPORTED_EXT; keeping it named makes future tuning safer. */
const SUPPORTED_EXT = new Set(['.pptx', '.pdf', '.ipynb', '.docx', '.rmd', '.html', '.htm', '.txt', '.md']);

const stats = { extracted: 0, skippedExt: 0, skippedDir: 0, failed: 0, bytesOut: 0 };
const failures = [];

/** Handles the shouldSkipDir step in this module’s workflow. */
function shouldSkipDir(name, extraPatterns) {
  const lower = name.toLowerCase();
  return SKIP_DIR_PATTERNS.some((p) => lower.includes(p)) || extraPatterns.some((p) => lower.includes(p));
}

/** Handles the walk step in this module’s workflow. */
function walk(dir, fileCb, extraSkip = []) {
  let entries;
  try {
    entries = readdirSync(dir, { withFileTypes: true });
  } catch {
    return;
  }
  for (const entry of entries) {
    if (entry.name.startsWith('.') && entry.name !== '.') continue;
    const full = join(dir, entry.name);
    if (entry.isDirectory()) {
      if (shouldSkipDir(entry.name, extraSkip)) {
        stats.skippedDir++;
        continue;
      }
      walk(full, fileCb, extraSkip);
    } else if (entry.isFile()) {
      fileCb(full);
    }
  }
}

/** Handles the extractPptx step in this module’s workflow. */
async function extractPptx(buf) {
  const zip = await JSZip.loadAsync(buf);
  const slideFiles = Object.keys(zip.files)
    .filter((n) => /^ppt\/slides\/slide\d+\.xml$/.test(n))
    .sort((a, b) => {
      const na = parseInt(a.match(/slide(\d+)\.xml/)[1], 10);
      const nb = parseInt(b.match(/slide(\d+)\.xml/)[1], 10);
      return na - nb;
    });
  const parts = [];
  for (const name of slideFiles) {
    const xml = await zip.files[name].async('string');
    const texts = [...xml.matchAll(/<a:t>([^<]*)<\/a:t>/g)].map((m) => m[1]);
    const slideNum = name.match(/slide(\d+)\.xml/)[1];
    parts.push(`--- Slide ${slideNum} ---\n${texts.join('\n')}`);
  }
  return parts.join('\n\n');
}

/** Handles the extractDocx step in this module’s workflow. */
async function extractDocx(buf) {
  const result = await mammoth.extractRawText({ buffer: buf });
  return result.value;
}

/** Handles the extractPdf step in this module’s workflow. */
async function extractPdf(buf) {
  const parser = new PDFParse({ data: buf });
  try {
    const result = await parser.getText();
    return result.text;
  } finally {
    await parser.destroy();
  }
}

/** Handles the extractIpynb step in this module’s workflow. */
function extractIpynb(buf) {
  const nb = JSON.parse(buf.toString('utf8'));
  const parts = [];
  for (const cell of nb.cells ?? []) {
    const src = Array.isArray(cell.source) ? cell.source.join('') : (cell.source ?? '');
    if (!src.trim()) continue;
    if (cell.cell_type === 'markdown') {
      parts.push(`[markdown]\n${src}`);
    } else if (cell.cell_type === 'code') {
      parts.push(`[code]\n${src}`);
      const outputs = cell.outputs ?? [];
      for (const out of outputs) {
        const text = out.text ? (Array.isArray(out.text) ? out.text.join('') : out.text) : null;
        if (text) parts.push(`[output]\n${text}`);
      }
    }
  }
  return parts.join('\n\n');
}

/** Handles the extractHtml step in this module’s workflow. */
function extractHtml(buf) {
  return htmlToText(buf.toString('utf8'), { wordwrap: false });
}

/** Handles the extractFile step in this module’s workflow. */
async function extractFile(path) {
  const ext = extname(path).toLowerCase();
  const buf = readFileSync(path);
  switch (ext) {
    case '.pptx': return extractPptx(buf);
    case '.docx': return extractDocx(buf);
    case '.pdf': return extractPdf(buf);
    case '.ipynb': return extractIpynb(buf);
    case '.html':
    case '.htm': return extractHtml(buf);
    case '.rmd':
    case '.txt':
    case '.md': return buf.toString('utf8');
    default: return null;
  }
}

/** Handles the run step in this module’s workflow. */
async function run() {
  for (const [bucket, srcDir] of Object.entries(SOURCES)) {
    const files = [];
    walk(srcDir, (f) => files.push(f), EXTRA_SKIP[bucket] ?? []);
    console.log(`[${bucket}] ${files.length} files under ${srcDir}`);

    for (const file of files) {
      const ext = extname(file).toLowerCase();
      if (!SUPPORTED_EXT.has(ext)) {
        stats.skippedExt++;
        continue;
      }
      const rel = relative(srcDir, file);
      const outPath = join(OUT_ROOT, bucket, rel) + '.txt';
      try {
        const text = await extractFile(file);
        if (!text || !text.trim()) {
          stats.skippedExt++;
          continue;
        }
        mkdirSync(dirname(outPath), { recursive: true });
        writeFileSync(outPath, text, 'utf8');
        stats.extracted++;
        stats.bytesOut += Buffer.byteLength(text, 'utf8');
      } catch (err) {
        stats.failed++;
        failures.push({ file, error: String(err?.message ?? err) });
      }
    }
  }

  mkdirSync(OUT_ROOT, { recursive: true });
  writeFileSync(
    join(OUT_ROOT, '_report.json'),
    JSON.stringify({ stats, failures, generatedAt: new Date().toISOString() }, null, 2),
  );
  console.log('\nExtraction complete:', stats);
  if (failures.length) console.log(`See ${join(OUT_ROOT, '_report.json')} for ${failures.length} failures.`);
}

await run();