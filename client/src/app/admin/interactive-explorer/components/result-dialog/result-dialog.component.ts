import { ChangeDetectionStrategy, Component, Inject } from '@angular/core';
import { MAT_DIALOG_DATA } from '@angular/material/dialog';
import { RunResult } from '../../scripts';

@Component({
  selector: 'ie-run-result',
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: 'result-dialog.component.html',
})
export class RunResultDialogComponent {
  constructor(@Inject(MAT_DIALOG_DATA) public data: RunResult) {
  }

}
