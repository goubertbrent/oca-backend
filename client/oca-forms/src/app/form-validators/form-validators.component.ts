import { ChangeDetectorRef, Component, forwardRef, Input } from '@angular/core';
import { ControlValueAccessor, NG_VALUE_ACCESSOR } from '@angular/forms';
import { FormValidator, ValidatorType } from '../interfaces/validators.interfaces';

@Component({
  selector: 'oca-form-validators',
  templateUrl: './form-validators.component.html',
  styleUrls: [ './form-validators.component.scss' ],
  providers: [ {
    provide: NG_VALUE_ACCESSOR,
    useExisting: forwardRef(() => FormValidatorsComponent),
    multi: true,
  } ],
})
export class FormValidatorsComponent implements ControlValueAccessor {

  @Input() set validators(value: FormValidator[]) {
    this._validators = value;
    this._changeDetectorRef.markForCheck();
  }

  get validators() {
    return this._validators;
  }

  @Input() validatorTypes: ValidatorType[];

  private _validators: FormValidator[];

  private onChange = (_: any) => {
  };
  private onTouched = () => {
  };

  constructor(private _changeDetectorRef: ChangeDetectorRef) {
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
    this._validators = values;
  }
}
