// Excel extraction: reads the canonical course spreadsheet and yields
// { rawTerm, term, klass, row } seeds. Column A = concept, column B = class.
import { readFileSync, existsSync } from 'node:fs';
import readXlsxFile from 'read-excel-file/node';
import { cleanTerm } from './util.mjs';

export const DEFAULT_XLSX = new URL('../Concepts to learn and include.xlsx', import.meta.url);

export async function extractRows(path = DEFAULT_XLSX) {
  const buf = readFileSync(path);
  const workbook = await readXlsxFile(buf);
  const grid = Array.isArray(workbook) && workbook.length && workbook[0] && Array.isArray(workbook[0].data)
    ? workbook[0].data
    : workbook;
  const rows = [];
  for (let i = 1; i < grid.length; i++) { // row 0 is the header ("Hot Keys" | "Class")
    const r = grid[i] || [];
    const rawTerm = r[0] == null ? null : String(r[0]).trim();
    const klass = r[1] == null ? null : String(r[1]).trim();
    if (!rawTerm) continue;
    rows.push({ rawTerm, term: cleanTerm(rawTerm), klass: klass || null, row: i + 1 });
  }
  return rows;
}

export async function extractIfAvailable(path = DEFAULT_XLSX) {
  if (!existsSync(path)) return null;
  return await extractRows(path);
}