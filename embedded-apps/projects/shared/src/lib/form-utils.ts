import { FormGroup } from '@angular/forms';

export function markFormGroupTouched(formGroup: FormGroup) {
  for (const control of Object.values(formGroup.controls)) {
    // setValue ensures the pristine/touched status of the ionic element is updated
    control.setValue(control.value);
    control.markAsTouched();
    control.markAsDirty();
  }
}
