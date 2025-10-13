import detectTone from '../EmotionToneDetector';

describe('detectTone', () => {
  test('detects positive tone', () => {
    const text = 'I am feeling absolutely amazing and wonderful today!';
    expect(detectTone(text)).toBe('positive');
  });

  test('detects negative tone', () => {
    const text = 'This is so bad and I am really sad about it.';
    expect(detectTone(text)).toBe('negative');
  });

  test('detects neutral tone when no keywords present', () => {
    const text = 'I went to the store to buy some groceries.';
    expect(detectTone(text)).toBe('neutral');
  });
});
