import { ChangeDetectionStrategy, Component, Inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { SERVICE_IDENTITY_REGEX } from '../../constants/rogerthat.constants';

export interface AutoAddedServiceDialogData {
  service: {
    service_email: string;
    app_id_pattern: string;
  };
}

@Component({
  selector: 'rcc-auto-added-service',
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: 'auto-added-service-dialog.component.html',
})
export class AutoAddedServiceDialogComponent {
  serviceEmailRegex = SERVICE_IDENTITY_REGEX;

  constructor(private dialogRef: MatDialogRef<AutoAddedServiceDialogComponent>,
              @Inject(MAT_DIALOG_DATA) public data: AutoAddedServiceDialogData) {
  }

  cancel() {
    this.dialogRef.close();
  }

  submit() {
    this.dialogRef.close(this.data.service);
  }
}
