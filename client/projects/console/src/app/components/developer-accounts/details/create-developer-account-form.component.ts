import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output, ViewChild } from '@angular/core';
import { NgForm } from '@angular/forms';
import { ApiRequestStatus } from '../../../../../framework/client/rpc';
import { CreateDeveloperAccountPayload } from '../../../interfaces';

@Component({
  selector: 'rcc-create-developer-account-form',
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: 'create-developer-account-form.component.html',
})
export class CreateDeveloperAccountFormComponent {
  @ViewChild('form', { static: false }) form: NgForm;
  @Input() status: ApiRequestStatus;
  @Output() create = new EventEmitter<CreateDeveloperAccountPayload>();
  developerAccount: CreateDeveloperAccountPayload = {
    account_email: '',
    account_password: null,
    google_credentials_json: null,
    name: '',
    type: 'ios',
  };

  isIos() {
    return this.developerAccount.type === 'ios';
  }

  submit() {
    if (this.form.form.valid) {
      this.create.emit({ ...this.developerAccount });
    }
  }
}
