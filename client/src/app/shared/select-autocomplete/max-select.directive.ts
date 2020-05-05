import { Directive, forwardRef, Input } from '@angular/core';
import { AbstractControl, NG_VALIDATORS, Validator } from '@angular/forms';

@Directive({
  selector: '[ocaMaxSelect]',
  providers: [
    { provide: NG_VALIDATORS, useExisting: forwardRef(() => MaxSelectDirective), multi: true },
  ],
})
export class MaxSelectDirective implements Validator {
  @Input('ocaMaxSelect') max: number;

  validate(ctrl: AbstractControl): { [ key: string ]: boolean } | null {
    const val = ctrl.value;
    return Array.isArray(val) && val.length > this.max ? { ocaMaxSelect: true } : null;
  }
}
