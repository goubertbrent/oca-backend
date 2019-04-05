import { Component, forwardRef, Input } from '@angular/core';
import { ControlValueAccessor, NG_VALUE_ACCESSOR } from '@angular/forms';
import { FormValidator, FormValidatorType, ValidatorType } from '../../interfaces/validators.interfaces';

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

  set validators(value: FormValidator[]) {
    if (value) {
      this.updateValues(value);
      this.onChange(value);
    }
  }

  get validators() {
    return this._validators || [];
  }

  @Input() validatorTypes: ValidatorType[];
  @Input() name: string;

  private _validators: FormValidator[];
  allowedTypes: ValidatorType[] = [];
  validatorNames: { [key in FormValidatorType]?: string };
  FormValidatorType = FormValidatorType;

  private onChange = (_: any) => {
  };
  private onTouched = () => {
  };

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

  addValidator(validatorType: FormValidatorType) {
    let validator: FormValidator;
    switch (validatorType) {
      case FormValidatorType.MAX:
        validator = { type: FormValidatorType.MAX, value: 2 };
        break;
      case FormValidatorType.MAXLENGTH:
        validator = { type: FormValidatorType.MAXLENGTH, value: 200 };
        break;
      case FormValidatorType.MIN:
        validator = { type: FormValidatorType.MIN, value: 2 };
        break;
      case FormValidatorType.MINLENGTH:
        validator = { type: FormValidatorType.MINLENGTH, value: 10 };
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
    this.validatorNames = this.validatorTypes.reduce((previousValue, currentValue) => ({
      ...previousValue,
      [ currentValue.type ]: currentValue.label,
    }), {});
  }
}
