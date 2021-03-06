import { ChangeDetectionStrategy, Component, Inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';


export interface SimpleDialogData {
  title?: string;
  message: string;
  ok: string;
  cancel?: string;
  required?: boolean;
  inputType?: string;
}

export interface SimpleDialogResultValue {
  submitted: boolean;
  value: string | null;
}

export type SimpleDialogResult = undefined | SimpleDialogResultValue;

@Component({
  selector: 'oca-simple-dialog',
  templateUrl: 'simple-dialog.component.html',
  styleUrls: ['simple-dialog.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SimpleDialogComponent {
  input = null;

  constructor(private dialogRef: MatDialogRef<SimpleDialogComponent>,
              @Inject(MAT_DIALOG_DATA) public data: SimpleDialogData) {
  }

  submit(submitted: boolean) {
    const result: SimpleDialogResult = { submitted, value: this.input };
    this.dialogRef.close(result);
  }
}
