import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  ElementRef,
  forwardRef,
  Input,
  ViewChild,
  ViewEncapsulation,
} from '@angular/core';
import { ControlValueAccessor, NG_VALUE_ACCESSOR } from '@angular/forms';
import { MatDatepicker, MatDatepickerInputEvent } from '@angular/material/datepicker';

@Component({
  selector: 'oca-date-time-input',
  templateUrl: './date-time-input.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
  providers: [{
    provide: NG_VALUE_ACCESSOR,
    useExisting: forwardRef(() => DateTimeInputComponent),
    multi: true,
  }],
})
export class DateTimeInputComponent implements ControlValueAccessor {
  @ViewChild(MatDatepicker, { static: true }) datePicker: MatDatepicker<Date>;
  @ViewChild('timeInput', { static: true }) timeInput: ElementRef<HTMLInputElement>;
  @Input() disabled: boolean;
  @Input() name: string;
  @Input() min: Date;
  @Input() max: Date;
  @Input() minError: string;
  @Input() maxError: string;
  @Input() required: boolean;
  @Input() dateLabel: string;
  @Input() timeLabel: string;

  date: Date | null;

  constructor(private changeDetectorRef: ChangeDetectorRef) {
  }

  registerOnChange(fn: any): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: any): void {
    this.onTouched = fn;
  }

  setDisabledState(isDisabled: boolean): void {
  }

  writeValue(obj: Date | null): void {
    if (obj !== this.date) {
      this.date = obj;
      this.changeDetectorRef.markForCheck();
    }
  }

  private onChange = (_: any) => {
  };
  private onTouched = () => {
  };

  onDateChange($event: MatDatepickerInputEvent<Date>) {
    if ($event.value) {
      const fullDate = new Date($event.value.getFullYear(), $event.value.getMonth(), $event.value.getDate());
      if (this.date) {
        fullDate.setHours(this.date.getHours());
        fullDate.setMinutes(this.date.getMinutes());
      }
      this.date = fullDate;
    } else {
      this.date = null;

    }
    this.onChange(this.date);
  }

  dateInputClicked() {
    if (!this.disabled) {
      this.datePicker.open();
    }
  }

  onTimeChanged($event: Date | null) {
    if (!this.date) {
      if (this.min) {
        this.date = new Date(this.min);
      } else {
        this.date = new Date();
      }
      this.date.setSeconds(0);
      this.date.setMilliseconds(0);
    }
    this.date.setHours($event?.getHours() ?? 0);
    this.date.setMinutes($event?.getMinutes() ?? 0);
    this.onChange(this.date);
    this.changeDetectorRef.markForCheck();
  }
}
