import { ChangeDetectionStrategy, Component, Inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';


export interface WhitelistDialogData {
  title: string;
  message: string;
  yes: string;
  no: string;
  cancel: string;
}

export interface WhitelistDialogResultValue {
  action: 'yes' | 'no' | 'cancel';
}

export type WhitelistDialogResult = undefined | WhitelistDialogResultValue;

@Component({
  selector: 'oca-whitelist-dialog',
  templateUrl: 'whitelist-dialog.component.html',
  styleUrls: ['whitelist-dialog.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class WhitelistDialogComponent {

  constructor(private dialogRef: MatDialogRef<WhitelistDialogComponent>,
              @Inject(MAT_DIALOG_DATA) public data: WhitelistDialogData) {
  }

  submit(action: 'yes' | 'no' | 'cancel') {
    const result: WhitelistDialogResult = { action };
    this.dialogRef.close(result);
  }
}
