import { DatePipe } from '@angular/common';
import { Injectable } from '@angular/core';
import { TranslateService } from '@ngx-translate/core';
import { EventFilterPeriod, EventListItem, EventMediaType, OcaEvent } from './events';

@Injectable({ providedIn: 'root' })
export class EventsService {

  constructor(private translate: TranslateService,
              private datePipe: DatePipe) {
  }

  convertEventList(events: OcaEvent[]): EventListItem[] {
    const results: EventListItem[] = [];
    for (const result of events) {
      let imageUrl: string | null = null;
      if (result.media && result.media.length) {
        const image = result.media.find(m => m.type === EventMediaType.IMAGE);
        if (image) {
          imageUrl = image.thumbnail_url;
        }
      }

      results.push({
        id: result.id,
        title: result.title,
        place: result.place,
        imageUrl,
        icon: 'image',
        startDate: new Date(result.start_date),
        calendarSummary: this.getCalendarSummary(result),
      });
    }
    return results;
  }


  getCalendarSummary(event: OcaEvent): string {
    const dayFormat = 'd MMMM y';
    const startDate = new Date(event.start_date);
    const endDate = new Date(event.end_date);
    if (this.isSameDay(startDate, endDate)) {
      return this.datePipe.transform(startDate, 'EEEE d MMMM y') as string;
    } else {
      const startStr = this.datePipe.transform(startDate, dayFormat);
      const endStr = this.datePipe.transform(endDate, dayFormat);
      return this.translate.instant('app.oca.from_x_until_y', { start: startStr, end: endStr });
    }
  }

  isSameDay(date1: Date, date2: Date) {
    return date1.getFullYear() === date2.getFullYear() && date1.getMonth() === date2.getMonth() && date1.getDate() === date2.getDate();
  }

  getStartEndDate(period: EventFilterPeriod) {
    const today = new Date();
    let startDate = new Date();
    const endDate = new Date();
    startDate.setHours(0, 0, 0, 0);
    endDate.setHours(0, 0, 0, 0);
    switch (period) {
      case EventFilterPeriod.TODAY:
        endDate.setDate(endDate.getDate() + 1);
        break;
      case EventFilterPeriod.TOMORROW:
        startDate.setDate(startDate.getDate() + 1);
        endDate.setDate(endDate.getDate() + 2);
        break;
      case EventFilterPeriod.THIS_WEEKEND:
        startDate = this.getWeekendStart(today);
        endDate.setDate(startDate.getDate() + 3);
        break;
      case EventFilterPeriod.NEXT_7:
        endDate.setDate(startDate.getDate() + 7);
        break;
      case EventFilterPeriod.NEXT_30:
        endDate.setDate(startDate.getDate() + 30);
        break;
      case EventFilterPeriod.RANGE:
        endDate.setMonth(startDate.getMonth() + 12);
        break;
    }
    return { startDate, endDate };
  }

  /**
   * Friday 16:00, or current time if it's currently weekend
   */
  getWeekendStart(date: Date) {
    const day = date.getDay();
    const startDay = 5;
    if ([5, 6, 7].includes(day)) {
      if (day === 5) {
        date.setHours(16, 0, 0, 0);
      }
      return date;
    }
    const resultDate = new Date(date);
    resultDate.setDate(date.getDate() + (7 + startDay - date.getDay()) % 7);
    date.setHours(16, 0, 0, 0);
    return resultDate;
  }
}
