import { Component, EventEmitter, Input, Output } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { NextAction, NextActionSection, NextActionType, UINextAction } from '../../interfaces/forms';
import { EditNextActionDialogComponent } from '../edit-next-action-dialog/edit-next-action-dialog.component';

@Component({
  selector: 'oca-next-action-editor',
  templateUrl: './next-action-editor.component.html',
  styleUrls: [ './next-action-editor.component.scss' ],
})
export class NextActionEditorComponent {
  NextActionType = NextActionType;

  @Input() name: string;
  @Input() label?: string;
  @Input() value: NextAction;
  @Input() nextActions: UINextAction[] = [];
  @Output() changed = new EventEmitter<NextAction>();

  constructor(private dialog: MatDialog) {
  }

  compareAction(first: NextAction, second?: NextAction) {
    if (!second) {
      return first.type === NextActionType.NEXT;
    }
    const sameType = first.type === second.type;
    if (sameType && first.type === NextActionType.SECTION) {
      return first.section === (second as NextActionSection).section;
    }
    return sameType;
  }

  trackActions(index: number, action: NextAction) {
    return action.type === NextActionType.SECTION ? `${NextActionType.SECTION}_${action.section}` : action.type;
  }

  actionUpdated(action: NextAction) {
    if (action.type === NextActionType.URL) {
      this.openActionEditor();
    } else {
      this.changed.emit(action);
    }
  }

  openActionEditor() {
    this.dialog.open(EditNextActionDialogComponent, { data: { action: this.value } }).afterClosed().subscribe(result => {
      this.value = result;
      this.changed.emit(this.value);
    });
  }

}
