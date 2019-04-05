import { CdkDragDrop, moveItemInArray } from '@angular/cdk/drag-drop';
import { ChangeDetectionStrategy, Component, Inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material';
import { FormSection } from '../../interfaces/forms.interfaces';
import { deepCopy } from '../../../shared/util/misc';


@Component({
  selector: 'oca-arrange-sections-dialog',
  templateUrl: './arrange-sections-dialog.component.html',
  styleUrls: [ './arrange-sections-dialog.component.scss' ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ArrangeSectionsDialogComponent {
  list: FormSection[];

  constructor(@Inject(MAT_DIALOG_DATA) private data: FormSection[],
              private dialogRef: MatDialogRef<ArrangeSectionsDialogComponent>) {
    this.list = deepCopy(data);
  }

  drop(event: CdkDragDrop<any>) {
    moveItemInArray(this.list, event.previousIndex, event.currentIndex);
  }

  save() {
    this.dialogRef.close(this.list);
  }

}
