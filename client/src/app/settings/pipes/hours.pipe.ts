import { DatePipe } from '@angular/common';
import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'hours',
  pure: true,
})
export class HoursPipe extends DatePipe implements PipeTransform {

  transform(value: string, format?: string): string {
    const date = new Date();
    const hours = parseInt(value.substr(0, 2), 10);
    const minutes = parseInt(value.substr(2, 2), 10);
    date.setHours(hours);
    date.setMinutes(minutes);
    return super.transform(date, format || 'shortTime') as string;
  }

}
