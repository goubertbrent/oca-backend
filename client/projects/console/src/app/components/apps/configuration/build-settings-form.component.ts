import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { TranslateService } from '@ngx-translate/core';
import { ApiRequestStatus } from '../../../../../framework/client/rpc';
import { APP_LANGUAGES } from '../../../constants';
import { App, AppTypes, BuildSettings, FriendCaptions, RegistrationType, registrationTypes } from '../../../interfaces';
import { cloneDeep } from '../../../util';

@Component({
  selector: 'rcc-build-settings-form',
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: 'build-settings-form.component.html',
})
export class BuildSettingsFormComponent {
  RegistrationType = RegistrationType;
  registrationTypes = registrationTypes;
  friendsCaptions = FriendCaptions;
  languages = APP_LANGUAGES;
  @Input() app: App;
  @Input() status: ApiRequestStatus;
  @Input() updateStatus: ApiRequestStatus;
  @Output() save = new EventEmitter<BuildSettings>();

  constructor(private translate: TranslateService,
              private router: Router,
              private route: ActivatedRoute) {

  }

  private _buildSettings: BuildSettings;

  get buildSettings() {
    return this._buildSettings;
  }

  @Input() set buildSettings(value: BuildSettings) {
    this._buildSettings = cloneDeep(value);
  }

  isYsaaa(): boolean {
    return this.app.app_type === AppTypes.YSAAA;
  }

  getRegistrationTypeInfo(): string {
    const type = this.registrationTypes.find(t => t.value === this.buildSettings.registration_type);
    if (type) {
      const path = this.router.createUrlTree([ '..', 'app-settings' ], { relativeTo: this.route }).toString();
      const url = `<a href="${ path }" target="_blank">${this.translate.instant('rcc.app_settings')}</a>`;
      return this.translate.instant(type.description, { url: url });
    }
    return '';
  }

  submit() {
    this.save.emit({ ...this.buildSettings });
  }
}
