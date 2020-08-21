import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output } from '@angular/core';
import { ApiRequestStatus } from '../../../../../framework/client/rpc';
import { AppMetaData, Language, LANGUAGES } from '../../../interfaces';
import { cloneDeep } from '../../../util';

@Component({
  selector: 'rcc-store-listing-translations-form',
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: 'store-listing-translations-form.component.html',
})
export class StoreListingTranslationsFormComponent {
  languages: Language[];
  allMetaData: AppMetaData[]; // all languages
  metadata: AppMetaData; // selected language

  @Input() appMetaDataStatus: ApiRequestStatus;
  @Input() updateAppMetaDataStatus: ApiRequestStatus;
  @Output() update = new EventEmitter<AppMetaData>();

  get appMetaData(): AppMetaData[] {
    return this.allMetaData;
  }

  @Input()
  set appMetaData(allMetaData: AppMetaData[]) {
    this.allMetaData = allMetaData;
    const codes = allMetaData.map(m => m.language);
    this.languages = codes.map(code => <Language>LANGUAGES.find(lang => lang.code === code));
    this.metadata = this.getLanguageMetaData(null);
  }

  languageChanged(lang: string) {
    this.metadata = this.getLanguageMetaData(lang);
  }

  getLanguageMetaData(languageCode: string | null): AppMetaData {
    let metadata;

    if (languageCode) {
      metadata = <AppMetaData>this.appMetaData.find((m: AppMetaData) => m.language === languageCode);
    } else {
      metadata = <AppMetaData>this.appMetaData[ 0 ];
    }
    return cloneDeep(metadata);
  }

  updateMetaData() {
    this.update.emit(cloneDeep(this.metadata));
  }
}
