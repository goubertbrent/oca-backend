/* tslint:disable:directive-selector no-host-metadata-property */
/**
 * From https://github.com/angular/angular/commit/3e685f98c666fcb9f0556ccb65d4b40716ac2985#diff-d60c63de232466b99bc9f5ab2bb39430
 */
import { Directive, forwardRef, Input, OnChanges, Provider, SimpleChanges } from '@angular/core';
import { AbstractControl, NG_VALIDATORS, ValidationErrors, Validator, ValidatorFn, Validators } from '@angular/forms';

export const MIN_VALIDATOR: Provider = {
  provide: NG_VALIDATORS,
  useExisting: forwardRef(() => MinValidator),
  multi: true,
};

/**
 * A directive which installs the {@link MinValidator} for any `formControlName`,
 * `formControl`, or control with `ngModel` that also has a `min` attribute.
 */
@Directive({
  selector: '[min][formControlName],[min][formControl],[min][ngModel]',
  providers: [ MIN_VALIDATOR ],
  host: { '[attr.min]': 'min ? min : null' },
})
export class MinValidator implements Validator, OnChanges {
  @Input() min: string | number;
  private _validator: ValidatorFn;
  private _onChange: () => void;

  ngOnChanges(changes: SimpleChanges): void {
    if ('min' in changes) {
      this._createValidator();
      if (this._onChange) {
        this._onChange();
      }
    }
  }

  validate(c: AbstractControl): ValidationErrors | null {
    return this._validator(c);
  }

  registerOnValidatorChange(fn: () => void): void {
    this._onChange = fn;
  }

  private _createValidator(): void {
    this._validator = Validators.min(typeof this.min === 'number' ? this.min : parseInt(this.min, 10));
  }
}


export const MAX_VALIDATOR: Provider = {
  provide: NG_VALIDATORS,
  useExisting: forwardRef(() => MaxValidator),
  multi: true,
};

/**
 * A directive which installs the {@link MaxValidator} for any `formControlName`,
 * `formControl`, or control with `ngModel` that also has a `min` attribute.
 */
@Directive({
  selector: '[max][formControlName],[max][formControl],[max][ngModel]',
  providers: [ MAX_VALIDATOR ],
  host: { '[attr.max]': 'max ? max : null' },
})
export class MaxValidator implements Validator, OnChanges {
  @Input() max: string | number;
  private _validator: ValidatorFn;
  private _onChange: () => void;

  ngOnChanges(changes: SimpleChanges): void {
    if ('max' in changes) {
      this._createValidator();
      if (this._onChange) {
        this._onChange();
      }
    }
  }

  validate(c: AbstractControl): ValidationErrors | null {
    return this._validator(c);
  }

  registerOnValidatorChange(fn: () => void): void {
    this._onChange = fn;
  }

  private _createValidator(): void {
    this._validator = Validators.max(typeof this.max === 'number' ? this.max : parseInt(this.max, 10));
  }
}
