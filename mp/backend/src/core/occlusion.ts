// Image-occlusion rendering: inject a mask (question side) or a reveal
// highlight (answer side) into a generated diagram SVG.
export interface Region { x: number; y: number; w: number; h: number }

export function occlusionSvg(svg: string, region: Region, revealed: boolean): string {
  const overlay = revealed
    ? `<rect x="${region.x - 3}" y="${region.y - 3}" width="${region.w + 6}" height="${region.h + 6}" rx="11" fill="none" stroke="#7dffb0" stroke-width="2.5" opacity="0.9"/>`
    : `<g><rect x="${region.x - 3}" y="${region.y - 3}" width="${region.w + 6}" height="${region.h + 6}" rx="11" fill="#0d2638" stroke="#ffd97a" stroke-width="1.6"/>` +
      `<text x="${region.x + region.w / 2}" y="${region.y + region.h / 2 + 5}" text-anchor="middle" fill="#ffd97a" font-size="15">?</text></g>`;
  return svg.replace('</svg>', overlay + '</svg>');
}
