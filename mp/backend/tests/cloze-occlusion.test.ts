import { describe, expect, it } from 'vitest';
import { clozeAnswers, clozeBack, clozeFront, isValidCloze, parseCloze } from '../src/core/cloze';
import { occlusionSvg } from '../src/core/occlusion';

describe('Cloze deletion rendering', () => {
  const text = 'CALCULATE is the only function that {{c1::transforms row context into filter context}}.';

  it('parses text and blank segments', () => {
    const segs = parseCloze(text);
    expect(segs).toHaveLength(3);
    expect(segs[1]).toMatchObject({ type: 'blank', text: 'transforms row context into filter context' });
  });

  it('front hides the answer; back reveals it', () => {
    expect(clozeFront(text)).toContain('[…]');
    expect(clozeFront(text)).not.toContain('transforms row context');
    expect(clozeBack(text)).toContain('transforms row context into filter context');
    expect(clozeBack(text)).not.toContain('{{');
  });

  it('supports hints ({{c1::answer::hint}})', () => {
    const hinted = 'Power is {{c1::1 − β::probability}}.';
    expect(clozeFront(hinted)).toContain('[probability]');
    expect(clozeAnswers(hinted)).toEqual(['1 − β']);
  });

  it('handles multiple blanks and validates', () => {
    const multi = '{{c1::HDFS}} stores blocks; {{c1::YARN}} allocates resources.';
    expect(clozeAnswers(multi)).toEqual(['HDFS', 'YARN']);
    expect(isValidCloze(multi)).toBe(true);
    expect(isValidCloze('no blanks here')).toBe(false);
  });
});

describe('Image occlusion rendering', () => {
  const svg = '<svg viewBox="0 0 720 420"><rect x="10" y="10" width="100" height="40"/></svg>';
  const region = { x: 10, y: 10, w: 100, h: 40 };

  it('masks the region on the question side', () => {
    const out = occlusionSvg(svg, region, false);
    expect(out).toContain('fill="#0d2638"');
    expect(out).toContain('>?</text>');
    expect(out.indexOf('</svg>')).toBeGreaterThan(out.indexOf('fill="#0d2638"'));
  });

  it('highlights the region on reveal', () => {
    const out = occlusionSvg(svg, region, true);
    expect(out).toContain('stroke="#7dffb0"');
    expect(out).not.toContain('>?</text>');
  });
});
