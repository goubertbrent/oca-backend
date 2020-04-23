import { FormArray, FormGroup } from '@angular/forms';

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
