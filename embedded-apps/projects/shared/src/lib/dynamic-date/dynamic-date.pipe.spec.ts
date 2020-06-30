import { DatePipe } from '@angular/common';
import { DynamicDatePipe } from './dynamic-date.pipe';

describe('DynamicDatePipe', () => {
  const now = new Date();
  const datePipe = new DatePipe('en');
  const pipe = new DynamicDatePipe('en');
  it('Should return time when date is on same day', () => {
    expect(pipe.transform(now)).toEqual(datePipe.transform(now, 'shortTime'));
  });
  it('Should return day name when date is on different day than today', () => {
    const lastWeek = new Date();
    lastWeek.setDate(now.getDate() - 6);
    expect(pipe.transform(lastWeek)).toEqual(datePipe.transform(lastWeek, 'EEE'));
  });
  it('Should return short date when date is more than a week ago', () => {
    const twoWeeksAgo = new Date();
    twoWeeksAgo.setDate(now.getDate() - 8);
    expect(pipe.transform(twoWeeksAgo)).toEqual(datePipe.transform(twoWeeksAgo, 'shortDate'));
  });
  it('Should include time for dates longer than a week ago', () => {
    const twoWeeksAgo = new Date();
    twoWeeksAgo.setDate(now.getDate() - 8);
    expect(pipe.transform(twoWeeksAgo, true)).toEqual(datePipe.transform(twoWeeksAgo, 'short'));
  });
  it('Should include time for less than a week ago', () => {
    const lastWeek = new Date();
    lastWeek.setDate(now.getDate() - 6);
    expect(pipe.transform(lastWeek, true)).toEqual(datePipe.transform(lastWeek, 'short'));
  });
});
