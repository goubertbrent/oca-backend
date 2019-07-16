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
import { MatDatepickerInputEvent } from '@angular/material/datepicker';

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
      this.setTimeInput();
      this.changeDetectorRef.markForCheck();
    }
  }

  onTimeChange() {
    if (!this.date) {
      if (this.min) {
        this.date = new Date(this.min);
      } else {
        this.date = new Date();
      }
      this.date.setSeconds(0);
      this.date.setMilliseconds(0);
    }
    const timeDate = this.timeInput.nativeElement.valueAsDate as Date | undefined;
    if (timeDate) {
      this.date.setHours(timeDate.getUTCHours());
      this.date.setMinutes(timeDate.getUTCMinutes());
    }
    this.onChange(this.date);
    this.changeDetectorRef.markForCheck();
  }

  private setTimeInput() {
    if (this.date) {
      const d = new Date(0);
      d.setUTCHours(this.date.getHours());
      d.setUTCMinutes(this.date.getMinutes());
      this.timeInput.nativeElement.valueAsDate = d;
    } else {
      this.timeInput.nativeElement.value = '';
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
}
