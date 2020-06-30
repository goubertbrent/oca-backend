import { DatePipe } from '@angular/common';
import { Pipe, PipeTransform } from '@angular/core';

const WEEK_MILLIS = 7 * 24 * 3600 * 1000;

@Pipe({
  name: 'dynamicDate',
  pure: true,
})
export class DynamicDatePipe extends DatePipe implements PipeTransform {

  // @ts-ignore
  transform(value: Date | string | number, includeTime?: boolean): string | null {
    const now = new Date();
    const date = value instanceof Date ? value : new Date(value);
    let format = includeTime ? 'short' : 'mediumDate';
    if (now.getFullYear() === date.getFullYear() && now.getMonth() === date.getMonth() && now.getDate() === date.getDate()) {
      // Same day
      format = 'shortTime';
    } else if (now.getTime() - date.getTime() < WEEK_MILLIS) {
      // Less than a week ago
      format = includeTime ? 'short' : 'EEE';
    }
    return super.transform(date, format);
  }
}
