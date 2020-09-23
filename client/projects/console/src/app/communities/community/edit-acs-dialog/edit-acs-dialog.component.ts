import { ChangeDetectionStrategy, Component, Inject, OnInit } from '@angular/core';
import { FormBuilder, Validators } from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { IFormBuilder, IFormGroup } from '@rxweb/types';
import { AutoConnectedService } from '../communities';

export interface EditAutoConnectedServiceDialogData {
  isNew: boolean;
  acs: AutoConnectedService;
}

@Component({
  selector: 'rcc-edit-acs-dialog',
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: 'edit-acs-dialog.component.html',
  styles: [` mat-select, mat-form-field {
    width: 300px;
  }`],
})
export class EditAutoConnectedServiceDialogComponent implements OnInit {
  isNew: boolean;
  serviceFormGroup: IFormGroup<AutoConnectedService>;
  private formBuilder: IFormBuilder;

  constructor(private dialogRef: MatDialogRef<EditAutoConnectedServiceDialogComponent>,
              formBuilder: FormBuilder,
              @Inject(MAT_DIALOG_DATA) private data: EditAutoConnectedServiceDialogData) {
    this.formBuilder = formBuilder;
  }

  ngOnInit() {
    this.isNew = this.data.isNew;
    this.serviceFormGroup = this.formBuilder.group<AutoConnectedService>({
      service_email: [this.data.acs.service_email, Validators.required],
      removable: [this.data.acs.removable],
    });
  }

  cancel() {
    this.dialogRef.close();
  }

  submit() {
    if (this.serviceFormGroup.valid) {
      this.dialogRef.close(this.serviceFormGroup.value);
    }
  }

}
