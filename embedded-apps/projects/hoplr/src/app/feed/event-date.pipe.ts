import { DatePipe } from '@angular/common';
import { Pipe, PipeTransform } from '@angular/core';
import { TranslateService } from '@ngx-translate/core';
import { HoplrEvent } from '../hoplr';

export function isSameDay(date1: Date, date2: Date) {
  return date1.getFullYear() === date2.getFullYear() && date1.getMonth() === date2.getMonth() && date1.getDate() === date2.getDate();
}

@Pipe({
  name: 'eventDate',
  pure: true,
})
export class EventDatePipe implements PipeTransform {

  constructor(private translate: TranslateService,
              private datePipe: DatePipe) {
  }

  transform(value: HoplrEvent): string {
    const dayFormat = 'EEEE d MMMM HH:mm';
    const startDate = new Date(value.data.From);
    const endDate = new Date(value.data.Until);
    const start = this.datePipe.transform(startDate, dayFormat) as string;
    if (isSameDay(startDate, endDate)) {
      const end = this.datePipe.transform(endDate, 'HH:mm') as string;
      return `${start} - ${end}`;
    } else {
      const endStr = this.datePipe.transform(endDate, dayFormat);
      return `${start} - ${endStr}`;
    }
  }

}
