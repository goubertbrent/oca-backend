import { TruncatePipe } from './truncate.pipe';

describe('TruncatePipe', () => {
  it('Should truncate a longer in length than the limit', () => {
    const pipe = new TruncatePipe();
    expect(pipe.transform('123456789', 5)).toBe('12345…');
  });
  it('Should not truncate a shorter in length than the limit', () => {
    const pipe = new TruncatePipe();
    expect(pipe.transform('123456789', 10)).toBe('123456789');
  });
  it('Should not truncate equal in length to the limit', () => {
    const pipe = new TruncatePipe();
    expect(pipe.transform('123456789', 9)).toBe('123456789');
  });
  it('Should not error when supplied with null', () => {
    const pipe = new TruncatePipe();
    expect(pipe.transform(null, 10)).toBe('');
  });
});
