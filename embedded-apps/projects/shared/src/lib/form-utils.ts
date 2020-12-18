import { FormGroup } from '@angular/forms';

/**
 * Marks a FormGroup and any nested FormGroup's as dirty and touched
 */
export function markFormGroupTouched(formGroup: FormGroup) {
  for (const control of Object.values(formGroup.controls)) {
    if (control instanceof FormGroup) {
      markFormGroupTouched(control);
    }
    control.markAsTouched();
    control.markAsDirty();
  }
}
