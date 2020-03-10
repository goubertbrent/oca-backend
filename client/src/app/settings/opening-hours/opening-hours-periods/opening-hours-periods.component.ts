import { FormStyle, getLocaleDayNames, TranslationWidth, WeekDay } from '@angular/common';
import {
  ChangeDetectionStrategy,
  Component,
  EventEmitter,
  Inject,
  Input,
  LOCALE_ID,
  OnChanges,
  Output,
  SimpleChange,
} from '@angular/core';
import { OpeningPeriod } from '../../../shared/interfaces/oca';
import { formatDateToHours, parseHours } from '../../../shared/time-picker/time-picker.component';

interface PeriodMapping {
  day: WeekDay;
  name: string;
  periods: OpeningPeriod[];
}

const DAY_SORT_MAPPING: { [T in WeekDay]: WeekDay } = {
  0: 6,
  1: 0,
  2: 1,
  3: 2,
  4: 3,
  5: 4,
  6: 5,
};

@Component({
  selector: 'oca-opening-hours-periods',
  templateUrl: './opening-hours-periods.component.html',
  styleUrls: ['./opening-hours-periods.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class OpeningHoursPeriodsComponent implements OnChanges {
  @Input() periodsAlwaysVisible = false;
  @Input() periods: OpeningPeriod[];
  @Output() changed = new EventEmitter<OpeningPeriod[]>();

  showPeriods = false;
  periodsPerDay: PeriodMapping[] = [];
  private dayNames: string[];

  constructor(@Inject(LOCALE_ID) private currentLocale: string) {
    this.dayNames = getLocaleDayNames(this.currentLocale, FormStyle.Standalone, TranslationWidth.Wide);
  }

  ngOnChanges(changes: { [P in keyof this]: SimpleChange }): void {
    if (changes.periods && this.periods) {
      this.periodsPerDay = this.dayNames.map((dayName, index) => ({ day: index, name: dayName, periods: [], summary: '' }));
      for (const period of this.periods) {
        this.periodsPerDay[ period.open.day ].periods.push(period);
      }
      this.periodsPerDay.sort((first, second) => DAY_SORT_MAPPING[ first.day ] - DAY_SORT_MAPPING[ second.day ]);
      this.setPeriodsVisible();
    }
  }

  setChanged() {
    const periods: OpeningPeriod[] = [];
    for (const mapping of this.periodsPerDay) {
      periods.push(...mapping.periods);
    }
    this.setPeriodsVisible();
    this.changed.emit(periods);
  }

  addHours(mapping: PeriodMapping) {
    mapping.periods.push({
      open: { day: mapping.day, time: '0800' },
      close: { day: mapping.day, time: '1700' },
    });
    this.setChanged();
  }

  deleteHours(period: PeriodMapping, hours: OpeningPeriod) {
    period.periods = period.periods.filter(p => p !== hours);
    this.setChanged();
  }

  doShowHours() {
    this.showPeriods = true;
  }

  trackPeriodByDay(index: number, item: PeriodMapping) {
    return item.day;
  }

  setTime(hours: OpeningPeriod, openOrClose: 'open' | 'close', newValue: string) {
    const updatedHour = parseHours(newValue);
    hours[ openOrClose ].time = formatDateToHours(updatedHour, '');
    this.setChanged();
  }

  trackHours(index: number, value: OpeningPeriod) {
    return index;
  }

  private setPeriodsVisible() {
    this.showPeriods = this.periodsAlwaysVisible || this.periods.length > 0;
  }
}
