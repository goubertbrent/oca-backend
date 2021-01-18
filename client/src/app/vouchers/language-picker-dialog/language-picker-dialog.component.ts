import { ChangeDetectionStrategy, Component } from '@angular/core';
import { FormControl, Validators } from '@angular/forms';
import { MatDialogRef } from '@angular/material/dialog';
import { LANGUAGES } from '../../../../projects/console/src/app/interfaces';

@Component({
  selector: 'oca-language-picker-dialog',
  templateUrl: './language-picker-dialog.component.html',
  styleUrls: ['./language-picker-dialog.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class LanguagePickerDialogComponent {
  languages = LANGUAGES;
  formControl = new FormControl(null, Validators.required);

  constructor(private dialogRef: MatDialogRef<LanguagePickerDialogComponent>) {
  }

  submit() {
    if (this.formControl.valid) {
      this.dialogRef.close(this.formControl.value);
    }
  }
}
