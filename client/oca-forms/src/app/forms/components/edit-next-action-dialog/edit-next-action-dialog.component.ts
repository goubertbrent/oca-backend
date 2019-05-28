import { ChangeDetectionStrategy, Component, Inject } from '@angular/core';
import { NgForm } from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { deepCopy } from '../../../shared/util/misc';
import { NextAction, NextActionType } from '../../interfaces/forms';

@Component({
  selector: 'oca-edit-next-action-dialog',
  templateUrl: './edit-next-action-dialog.component.html',
  styleUrls: [ './edit-next-action-dialog.component.scss' ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class EditNextActionDialogComponent {
  nextAction: NextAction;
  NextActionType = NextActionType;

  constructor(@Inject(MAT_DIALOG_DATA) private data: { action: NextAction },
              private dialogRef: MatDialogRef<EditNextActionDialogComponent, NextAction>) {
    this.nextAction = deepCopy(data.action);
  }

  isValid() {
    switch (this.nextAction.type) {
      case NextActionType.URL:
        return this.nextAction.url && this.nextAction.url.trim() !== '';
    }
    return true;
  }

  close() {
    // Close with original data
    this.dialogRef.close(this.data.action);
  }

  submit(ngForm: NgForm) {
    if (ngForm.form.valid && this.isValid()) {
      this.dialogRef.close(this.nextAction);
    }
  }

}
