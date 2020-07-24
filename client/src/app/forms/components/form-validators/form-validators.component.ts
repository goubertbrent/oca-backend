import { ChangeDetectionStrategy, ChangeDetectorRef, Component, forwardRef, Input } from '@angular/core';
import { ControlValueAccessor, NG_VALUE_ACCESSOR } from '@angular/forms';
import { MatDatepickerInputEvent } from '@angular/material/datepicker';
import { updateItem } from '../../../shared/util';
import { FormComponentType } from '../../interfaces/enums';
import { DatetimeValue } from '../../interfaces/form-values';
import { FormValidator, FormValidatorType, MaxDateValidator, MinDateValidator, ValidatorType } from '../../interfaces/validators';

@Component({
  selector: 'oca-form-validators',
  templateUrl: './form-validators.component.html',
  styleUrls: [ './form-validators.component.scss' ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  providers: [ {
    provide: NG_VALUE_ACCESSOR,
    useExisting: forwardRef(() => FormValidatorsComponent),
    multi: true,
  } ],
})
export class FormValidatorsComponent implements ControlValueAccessor {

  set validators(value: FormValidator[]) {
    if (value) {
      this.updateValues(value);
      this.onChange(value);
    }
  }

  get validators() {
    return this._validators || [];
  }

  @Input() componentType: FormComponentType;
  @Input() validatorTypes: ValidatorType[];
  @Input() name: string;

  private _validators: FormValidator[];
  allowedTypes: ValidatorType[] = [];
  validatorNames: { [key in FormValidatorType]?: string };
  valueNames: { [key in FormValidatorType]?: string };
  FormValidatorType = FormValidatorType;
  FormComponentType = FormComponentType;

  private onChange = (_: any) => {
  };
  private onTouched = () => {
  };

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

  writeValue(values: FormValidator[]): void {
    if (values !== this.validators) {
      this.updateValues(values);
    }
  }

  addValidator(validatorType: ValidatorType) {
    let validator: FormValidator;
    switch (validatorType.type) {
      case FormValidatorType.MAX:
        validator = { type: FormValidatorType.MAX, value: validatorType.value as number };
        break;
      case FormValidatorType.MAXLENGTH:
        validator = { type: FormValidatorType.MAXLENGTH, value: validatorType.value as number };
        break;
      case FormValidatorType.MINDATE:
        validator = { type: validatorType.type, ...dateToDatetimeValue(validatorType.value as Date) };
        break;
      case FormValidatorType.MAXDATE:
        validator = { type: validatorType.type, ...dateToDatetimeValue(validatorType.value as Date) };
        break;
      case FormValidatorType.MIN:
        validator = { type: FormValidatorType.MIN, value: validatorType.value as number };
        break;
      case FormValidatorType.MINLENGTH:
        validator = { type: FormValidatorType.MINLENGTH, value: validatorType.value as number };
        break;
      default:
        return;
    }
    this.validators = [ ...this.validators, validator ];
  }

  removeValidator(validator: FormValidator) {
    this.validators = this.validators.filter(v => v.type !== validator.type);
  }

  trackByType(index: number, item: FormValidator) {
    return item.type;
  }

  private updateValues(value: FormValidator[] | null) {
    this._validators = value ? [ ...value ] : [];
    const currentTypes = this._validators.map(v => v.type);
    // @ts-ignore
    this.allowedTypes = this.validatorTypes.filter(v => !currentTypes.includes(v.type));
    this.validatorNames = {};
    this.valueNames = {};
    for (const validator of this.validatorTypes) {
      this.validatorNames[ validator.type ] = validator.label;
      this.valueNames[ validator.type ] = validator.value_label || 'oca.number';
    }
    this.changeDetectorRef.markForCheck();
  }

  setDate(event: MatDatepickerInputEvent<any>, validator: MinDateValidator | MaxDateValidator) {
    if (event.value instanceof Date) {
      validator = { ...validator, ...dateToDatetimeValue(event.value as Date) };
    }
    this.validators = updateItem(this.validators, validator, 'type');
  }

  getDateValue(validator: MinDateValidator | MaxDateValidator) {
    return datetimeValueToDate(validator);
  }
}

function datetimeValueToDate(val: DatetimeValue): Date {
  return new Date(val.year, val.month - 1, val.day, val.hour, val.minute);
}

function dateToDatetimeValue(date: Date): DatetimeValue {
  // Time not supported
  return {
    year: date.getFullYear(),
    month: date.getMonth() + 1,
    day: date.getDate(),
    hour: 0,
    minute: 0,
  };
}
