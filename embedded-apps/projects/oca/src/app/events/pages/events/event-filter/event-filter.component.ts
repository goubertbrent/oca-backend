import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output, ViewChild } from '@angular/core';
import { NgForm } from '@angular/forms';
import { Store } from '@ngrx/store';
import { EventFilterPeriod, GetEventsParams } from '../../../events';
import { EventsService } from '../../../events.service';
import { EventsState } from '../../../events.state';

@Component({
  selector: 'app-event-filter',
  templateUrl: './event-filter.component.html',
  styleUrls: ['./event-filter.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class EventFilterComponent {
  @Input() query: string | null = null;
  @Input() startDate: string;
  @Input() endDate: string;
  @Input() selectedPeriod: EventFilterPeriod;

  @Output() searched = new EventEmitter<GetEventsParams>();
  @Output() delayedSearch = new EventEmitter<GetEventsParams>();
  @ViewChild('form') form: NgForm;
  DATE_RANGE = EventFilterPeriod.RANGE;
  minStartDate = new Date().toISOString();
  yearValues = [new Date().getFullYear(), new Date().getFullYear() + 1];

  periods = [
    { key: EventFilterPeriod.TODAY, label: 'app.oca.today', params: null },
    { key: EventFilterPeriod.TOMORROW, label: 'app.oca.tomorrow', params: null },
    { key: EventFilterPeriod.THIS_WEEKEND, label: 'app.oca.this_weekend', params: null },
    { key: EventFilterPeriod.NEXT_7, label: 'app.oca.next_x_days', params: { days: 7 } },
    { key: EventFilterPeriod.NEXT_30, label: 'app.oca.next_x_days', params: { days: 30 } },
    { key: EventFilterPeriod.RANGE, label: 'app.oca.specific_date', params: null },
  ];

  constructor(private store: Store<EventsState>,
              private eventsService: EventsService) {
  }

  submitSearch(immediate: boolean) {
    if (this.form.form.valid) {
      const params = {
        query: this.query,
        endDate: this.endDate,
        startDate: this.startDate,
        period: this.selectedPeriod,
      };
      if (immediate) {
        this.searched.emit(params);
      } else {
        this.delayedSearch.emit(params);
      }
    }
  }

  periodChanged(period: EventFilterPeriod) {
    const { startDate, endDate } = this.eventsService.getStartEndDate(period);
    this.startDate = startDate.toISOString();
    this.endDate = endDate.toISOString();
    this.selectedPeriod = period;
    this.submitSearch(true);
  }

  setStartDate(value: string) {
    const startDate = new Date(value);
    this.startDate = startDate.toISOString();
    if (startDate > new Date(this.endDate)) {
      this.setEndDate(value);
    } else {
      this.submitSearch(true);
    }
  }

  setEndDate(value: string) {
    const end = new Date(value);
    end.setHours(23, 59, 59, 999);
    this.endDate = end.toISOString();
    this.submitSearch(true);
  }

  queryChanged(value: string) {
    this.query = value;
    this.submitSearch(false);
  }
}
