import { ChangeDetectionStrategy, Component, Input, OnChanges, SimpleChanges } from '@angular/core';
import { EventDate } from '../../../events';
import { EventsService } from '../../../events.service';

@Component({
  selector: 'app-event-date-line',
  templateUrl: './event-date-line.component.html',
  styleUrls: ['./event-date-line.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class EventDateLineComponent implements OnChanges {
  @Input() hoursOnly = false;
  @Input() startDate: EventDate | Date;
  @Input() endDate: EventDate | Date;
  @Input() dateFormat = 'd MMM y H:mm';

  readonly hourFormat = 'H:mm';

  start: Date;
  end: Date;
  isSameDay = false;

  constructor(private eventsService: EventsService) {
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes.startDate || changes.endDate) {
      if (this.startDate && this.endDate) {
        this.start = this.getDate(this.startDate);
        this.end = this.getDate(this.endDate);
        this.isSameDay = this.eventsService.isSameDay(this.start, this.end);
      }
    }
  }

  private getDate(date: EventDate | Date): Date {
    if (date instanceof Date) {
      return date;
    } else {
      return new Date('date' in date ? date.date : date.datetime);
    }
  }
}
