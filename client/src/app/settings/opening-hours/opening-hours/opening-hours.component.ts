import { DatePipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output } from '@angular/core';
import { OpeningHourException, OpeningHours, OpeningPeriod } from '../../../shared/interfaces/oca';
import { HoursPipe } from '../../pipes/hours.pipe';

@Component({
  selector: 'oca-opening-hours',
  templateUrl: './opening-hours.component.html',
  styleUrls: ['./opening-hours.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class OpeningHoursComponent {
  @Input() openingHours: OpeningHours;
  @Input() isLoading: boolean;
  @Output() saved = new EventEmitter<OpeningHours>();
  @Output() hoursChanged = new EventEmitter<OpeningHours>();

  constructor(private hoursPipe: HoursPipe,
              private datePipe: DatePipe) {
  }

  updateDate(exception: OpeningHourException, property: 'start_date' | 'end_date', value: Date | null, index: number) {
    if (value) {
      exception[ property ] = this.datePipe.transform(value, 'yyyy-MM-dd') as string;
      this.updateExceptionPeriodsAtIndex(exception, index);
    }
  }

  updateExceptionPeriods(exception: OpeningHourException, $event: OpeningPeriod[], index: number) {
    this.updateExceptionPeriodsAtIndex({ ...exception, periods: $event }, index);
  }

  updateExceptionPeriodsAtIndex(exception: OpeningHourException, index: number) {
    const exceptions = this.openingHours.exceptional_opening_hours;
    exceptions[ index ] = exception;
    this.setChanged({ ...this.openingHours, exceptional_opening_hours: exceptions });
  }

  addException() {
    const today = new Date().toISOString().split('T')[ 0 ];
    const exception: OpeningHourException = { start_date: today, end_date: today, periods: [], description: null };
    this.setChanged({ ...this.openingHours, exceptional_opening_hours: [...this.openingHours.exceptional_opening_hours, exception] });
  }

  removeException(exception: OpeningHourException) {
    this.setChanged({
      ...this.openingHours,
      exceptional_opening_hours: this.openingHours.exceptional_opening_hours.filter(e => e !== exception),
    });
  }

  trackByIndex(index: number, element: any) {
    return index;
  }

  updatePeriods(periods: OpeningPeriod[]) {
    this.setChanged({ ...this.openingHours, periods });
  }

  private setChanged(openingHours: OpeningHours) {
    this.openingHours = openingHours;
    this.hoursChanged.next(this.openingHours);
  }
}
