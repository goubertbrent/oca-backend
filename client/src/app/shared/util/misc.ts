import { FormArray, FormGroup } from '@angular/forms';

export type DeepPartial<T> = {
    [P in keyof T]?: DeepPartial<T[P]>;
};

export function deepCopy<T extends object>(obj: T): T {
  return JSON.parse(JSON.stringify(obj));
}

export function markAllControlsAsDirty(formGroup: FormGroup | FormArray) {
  formGroup.markAsDirty();
  formGroup.markAsTouched();
  for (const control of Object.values(formGroup.controls)) {
    if (!control.valid) {
      control.markAsTouched();
      control.markAsDirty();
      control.updateValueAndValidity({ emitEvent: false });
      if (control instanceof FormGroup || control instanceof FormArray) {
        markAllControlsAsDirty(formGroup);
      }
    }
  }
}

export function parseNumber(number: string | null | undefined): number | null {
  if (!number) {
    return null;
  }
  const result = parseInt(number, 10);
  return isNaN(result) ? null : result;
}

/**
 * @example
 * // Returns 'Creme Brulee'
 * removeDiacritics('Crème Brulée')
 */
export function removeDiacritics(string: string): string {
  return string.normalize('NFD').replace(/[\u0300-\u036f]/g, '');
}
