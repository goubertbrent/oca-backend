import { ChangeDetectionStrategy, Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { NavController } from '@ionic/angular';
import { select, Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { CalendarType, EventDate, EventMediaType, EventPeriod, OcaEvent } from '../../events';
import { AddEventToCalendarAction } from '../../events.actions';
import { EventsState, getEventById, isAddingToCalendar } from '../../events.state';

interface EventTimeDetails {
  startDate: Date;
  endDate: Date | null;
  periods: EventPeriod[];
  hours: {
    from: Date;
    until: Date;
  }[];
}

@Component({
  selector: 'app-event-details',
  templateUrl: './event-details.page.html',
  styleUrls: ['./event-details.page.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class EventDetailsPage implements OnInit {
  event$: Observable<OcaEvent | undefined>;
  hasNoMedia$: Observable<boolean>;
  isAddingToCalendar$: Observable<boolean>;
  placeUrl$: Observable<string | undefined>;
  timeDetails$: Observable<EventTimeDetails | null>;
  CalendarType = CalendarType;
  now = new Date();

  constructor(private store: Store<EventsState>,
              private navController: NavController,
              private route: ActivatedRoute) {
  }

  ngOnInit() {
    const eventId: number = parseInt(this.route.snapshot.params.eventId, 10);
    this.event$ = this.store.pipe(select(getEventById, eventId));
    this.isAddingToCalendar$ = this.store.pipe(select(isAddingToCalendar));
    this.placeUrl$ = this.event$.pipe(map(e => e && `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(e.place)}`));
    this.hasNoMedia$ = this.event$.pipe(map(event => !event || event.media.every(m => m.type !== EventMediaType.IMAGE)));
    this.timeDetails$ = this.event$.pipe(map(event => {
      if (!event) {
        return null;
      }
      return {
        startDate: new Date(event.start_date),
        endDate: event.end_date ? new Date(event.end_date) : null,
        periods: event.periods.filter(p => this.isInPast(p.end)),
        hours: event.opening_hours.map(period => {
          const fromTime = parseHours(period.open);
          const untilTime = parseHours(period.close as string);
          // new Date(0,0,0) -> sunday 31 dec 1899 00:00:00
          return {
            from: new Date(0, 0, period.day, fromTime.hours, fromTime.minutes),
            until: new Date(0, 0, period.day, untilTime.hours, untilTime.minutes),
          };
        }),
      };
    }));
  }

  addToCalendar(event: OcaEvent) {
    // TODO events: should give options and not just use current date
    this.store.dispatch(new AddEventToCalendarAction({
      id: event.id,
      service_user_email: event.service_user_email,
      date: new Date().toISOString(),
    }));
  }

  goBack() {
    this.navController.back();
  }

  private isInPast(period: EventDate): boolean {
    if ('date' in period) {
      return this.now < new Date(period.date);
    } else {
      return this.now < new Date(period.datetime);
    }
  }
}


function parseHours(hours: string): { hours: number; minutes: number } {
  return { hours: parseInt(hours.substr(0, 2), 10), minutes: parseInt(hours.substr(3, 2), 10) };
}
