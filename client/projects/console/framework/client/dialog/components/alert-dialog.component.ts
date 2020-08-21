import { ChangeDetectionStrategy, Component, Inject, ViewEncapsulation } from '@angular/core';
import { MAT_DIALOG_DATA } from '@angular/material/dialog';
import { AlertDialogData } from '../dialog.interfaces';

@Component({
  selector: 'alert-dialog',
  templateUrl: 'alert-dialog.component.html',
  encapsulation: ViewEncapsulation.None,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AlertDialogComponent {
  constructor(@Inject(MAT_DIALOG_DATA) public data: AlertDialogData) {
  }
}
