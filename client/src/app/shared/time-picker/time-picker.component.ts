import { ChangeDetectionStrategy, ChangeDetectorRef, Component, forwardRef, Input } from '@angular/core';
import { ControlValueAccessor, NG_VALUE_ACCESSOR } from '@angular/forms';

export function parseHours(value: string): Date {
  const hours = new Date();
  const [hour, minutes] = value.split(':').map(part => parseInt(part, 10));
  hours.setUTCHours(hour, minutes, 0, 0);
  return hours;
}

export function formatDateToHours(date: Date, separator=':'): string {
  return `${date.getUTCHours().toString().padStart(2, '0')}${separator}${date.getUTCMinutes().toString().padStart(2, '0')}`;
}

@Component({
  selector: 'oca-time-picker',
  templateUrl: './time-picker.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  providers: [{
    provide: NG_VALUE_ACCESSOR,
    useExisting: forwardRef(() => TimePickerComponent),
    multi: true,
  }],
})
export class TimePickerComponent implements ControlValueAccessor {
  @Input() label?: string;
  @Input() required?: boolean;
  disabled = false;
  value: string | null;

  _min: string | null = null;

  @Input() set min(value: string | null) {
    this._min = value;
    this.maybeUpdateValue();
  }

  _max: string | null = null;

  @Input() set max(value: string | null) {
    this._max = value;
    this.maybeUpdateValue();
  }

  constructor(private changeDetectorRef: ChangeDetectorRef) {
  }


  setValueFromInput($event: Event) {
    const input = $event.target as HTMLInputElement;
    const date = input.valueAsDate;
    if (!date) {
      input.value = this.value as string;
      return;
    }
    this.setValue(date);
  }

  setValue(date: Date) {
    this.value = formatDateToHours(date);
    this.onChange(this.value);
  }

  registerOnChange(fn: any): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: any): void {
    this.onTouched = fn;
  }

  setDisabledState(isDisabled: boolean): void {
    this.disabled = isDisabled;
  }

  writeValue(value: string): void {
    this.value = value;
    this.changeDetectorRef.markForCheck();
  }

  private onChange = (_: any) => {
  };

  private onTouched = () => {
  };

  private maybeUpdateValue() {
    // Ensures the current value doesn't exceed the max and isn't lower than the min
    if (this.value) {
      const value = parseHours(this.value);
      if (this._min) {
        const minHours = parseHours(this._min);
        if (value <= minHours) {
          minHours.setMinutes(minHours.getMinutes() + 1);
          this.setValue(minHours);
        }
      }
      if (this._max) {
        const maxHours = parseHours(this._max);
        if (value >= maxHours) {
          maxHours.setMinutes(maxHours.getMinutes() - 1);
          this.setValue(maxHours);
        }
      }
    }
  }
}
