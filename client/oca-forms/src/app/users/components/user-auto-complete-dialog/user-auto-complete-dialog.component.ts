import { ChangeDetectionStrategy, Component, Inject, ViewEncapsulation } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material';
import { UserDetailsTO } from '../../interfaces';
import { UserAutocompleteComponent } from '../user-autocomplete/user-autocomplete.component';

export interface UserDialogData {
  title?: string;
  message: string;
  ok: string;
  cancel?: string;
}

@Component({
  selector: 'oca-user-auto-complete-dialog',
  templateUrl: './user-auto-complete-dialog.component.html',
  encapsulation: ViewEncapsulation.None,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class UserAutoCompleteDialogComponent {
  selectedUser: UserDetailsTO | null = null;

  constructor(private dialogRef: MatDialogRef<UserAutocompleteComponent>,
              @Inject(MAT_DIALOG_DATA) public data: UserDialogData) {
  }

  onOptionSelected(user: UserDetailsTO) {
    this.selectedUser = user;
  }

  close() {
    this.dialogRef.close(null);
  }

  submit() {
    this.dialogRef.close(this.selectedUser);
  }

}
