import { ChangeDetectionStrategy, Component, Input, ViewEncapsulation } from '@angular/core';
import { ApiRequestStatus } from '../../../../../framework/client/rpc';
import { APP_LANGUAGES } from '../../../constants';
import { NewsSettings } from '../../../interfaces';
import { cloneDeep } from '../../../util';

@Component({
  selector: 'rcc-news-settings-form',
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.Emulated,
  templateUrl: 'news-settings-form.component.html',
  styles: [`.image-card {
    display: inline-block;
    width: 250px;
    margin: 16px;
  }

  .image-container {
    height: 192px;
  }

  .image-card img {
    width: auto;
    max-height: 200px;
    max-width: 200px;
    margin-top: 0;
  }`],
})
export class NewsSettingsFormComponent {
  languages = APP_LANGUAGES;
  @Input() status: ApiRequestStatus;
  @Input() updateStatus: ApiRequestStatus;

  private _newsSettings: NewsSettings;

  get newsSettings() {
    return this._newsSettings;
  }

  @Input() set newsSettings(value: NewsSettings) {
    this._newsSettings = cloneDeep(value);
  }
}
