import { WeekDay } from '@angular/common';
import { ChangeDetectionStrategy, Component, forwardRef, Input } from '@angular/core';
import { ControlValueAccessor, NG_VALUE_ACCESSOR } from '@angular/forms';
import { MatSlideToggleChange } from '@angular/material/slide-toggle';
import { OpeningPeriod } from '../../../shared/interfaces/oca';
import { formatDateToHours, parseHours } from '../../../shared/time-picker/time-picker.component';
import { OPEN_24_HOURS_TIME } from '../../service-info/constants';


function isOpen24Hours(periods: OpeningPeriod[]): boolean {
  if (periods.length === 1) {
    const { open, close } = periods[ 0 ];
    return !close && open.time === OPEN_24_HOURS_TIME;
  }
  return false;
}

function getNextDay(time: WeekDay): WeekDay {
  return time < WeekDay.Saturday ? time + 1 : WeekDay.Sunday;
}

@Component({
  selector: 'oca-opening-hours-periods-editor',
  templateUrl: './opening-hours-periods-editor.component.html',
  styleUrls: ['./opening-hours-periods-editor.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  providers: [{
    provide: NG_VALUE_ACCESSOR,
    useExisting: forwardRef(() => OpeningHoursPeriodsEditorComponent),
    multi: true,
  }],
})
export class OpeningHoursPeriodsEditorComponent implements ControlValueAccessor {
  @Input() day: WeekDay;

  periods: OpeningPeriod[] = [];
  disabled = false;
  isOpen24Hours = false;

  registerOnChange(fn: any): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: any): void {
    this.onTouched = fn;
  }

  setDisabledState(isDisabled: boolean): void {
    this.disabled = isDisabled;
  }

  writeValue(value: OpeningPeriod[] | null): void {
    if (value) {
      this.isOpen24Hours = isOpen24Hours(value);
      this.periods = value;
    }
  }

  setChanged() {
    this.isOpen24Hours = isOpen24Hours(this.periods);
    this.onChange(this.periods);
  }

  trackHours(index: number, value: OpeningPeriod) {
    return index;
  }

  setOpenTime(hours: OpeningPeriod, newValue: string) {
    const updatedHour = parseHours(newValue);
    hours.open.time = formatDateToHours(updatedHour, '');
    this.setChanged();
  }

  setCloseTime(hours: OpeningPeriod, newValue: string) {
    const openTime = parseHours(hours.open.time);
    const closeTime = parseHours(newValue);
    hours.close = {
      day: openTime < closeTime ? hours.open.day : getNextDay(hours.open.day),
      time: formatDateToHours(closeTime, ''),
    };
    this.setChanged();
  }

  addHours() {
    this.periods.push({
      open: { day: this.day, time: '0800' },
      close: { day: this.day, time: '1700' },
    });
    this.setChanged();
  }

  deleteHours(hours: OpeningPeriod) {
    this.periods = this.periods.filter(p => p !== hours);
    this.setChanged();
  }

  toggleOpen24Hours($event: MatSlideToggleChange) {
    this.isOpen24Hours = $event.checked;
    this.periods.length = 0;
    if ($event.checked) {
      this.periods.push({ open: { time: OPEN_24_HOURS_TIME, day: this.day }, close: null });
    }
    this.setChanged();
  }

  private onChange = (value: any) => {
  };

  private onTouched = (value: any) => {
  };
}
