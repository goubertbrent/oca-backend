import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output } from '@angular/core';
import { ApiRequestStatus } from '../../../../../framework/client/rpc';
import { DeveloperAccount } from '../../../interfaces';

@Component({
  selector: 'rcc-edit-developer-account-form',
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: 'edit-developer-account-form.component.html',
})
export class EditDeveloperAccountFormComponent {
  @Input() status: ApiRequestStatus;
  @Output() save = new EventEmitter<DeveloperAccount>();

  private _developerAccount: DeveloperAccount;

  get developerAccount(): DeveloperAccount {
    return this._developerAccount;
  }

  @Input() set developerAccount(value: DeveloperAccount) {
    this._developerAccount = { ...value };
  }

  isIos() {
    return this.developerAccount.type === 'ios';
  }

  submit() {
    this.save.emit({ ...this.developerAccount });
  }

}
