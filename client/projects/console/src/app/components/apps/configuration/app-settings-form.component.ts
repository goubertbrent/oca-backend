import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output } from '@angular/core';
import { ApiRequestStatus } from '../../../../../framework/client/rpc';
import { AppSettings } from '../../../interfaces';
import { cloneDeep } from '../../../util';

@Component({
  selector: 'rcc-app-settings-form',
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: 'app-settings-form.component.html',
})
export class AppSettingsFormComponent {
  @Input() status: ApiRequestStatus;
  @Input() updateStatus: ApiRequestStatus;
  @Output() save = new EventEmitter<AppSettings>();

  private _appSettings: AppSettings;

  get appSettings() {
    return this._appSettings;
  }

  @Input() set appSettings(value: AppSettings) {
    this._appSettings = cloneDeep(value);
  }

  submit() {
    this.save.emit(this.appSettings);
  }
}
