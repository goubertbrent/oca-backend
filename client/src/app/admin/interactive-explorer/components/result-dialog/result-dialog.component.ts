import { ChangeDetectionStrategy, Component, Inject, ViewEncapsulation } from '@angular/core';
import { MAT_DIALOG_DATA } from '@angular/material/dialog';
import { RunResult } from '../../scripts';

@Component({
  selector: 'oca-script-run-result',
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
  templateUrl: 'result-dialog.component.html',
})
export class RunResultDialogComponent {
  constructor(@Inject(MAT_DIALOG_DATA) public data: RunResult) {
  }

}
