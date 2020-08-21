import { ChangeDetectionStrategy, Component, Inject, OnInit } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { PromptDialogData } from '../dialog.interfaces';

@Component({
  selector: 'prompt-dialog',
  templateUrl: 'prompt-dialog.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PromptDialogComponent implements OnInit {
  input: string;
  inputType: string;

  constructor(public dialogRef: MatDialogRef<PromptDialogComponent>,
              @Inject(MAT_DIALOG_DATA) public data: PromptDialogData) {
  }

  ngOnInit() {
    this.input = this.data.initialValue || '';
    this.inputType = this.data.inputType || 'text';
  }

  submit(submitted: boolean) {
    this.dialogRef.close({
      submitted: submitted,
      value: submitted ? this.input : null,
    });
  }
}
