import { ChangeDetectionStrategy, Component, EventEmitter, Input, OnChanges, Output, SimpleChanges } from '@angular/core';
import { TranslateService } from '@ngx-translate/core';
import { of } from 'rxjs';
import { ApiRequestStatus } from '../../../../../framework/client/rpc';
import {
  App,
  AppMetaData,
  BUILD_TYPE_STRINGS,
  BuildType,
  BulkUpdatePayload,
  CheckListItem,
  Language,
  LANGUAGES,
} from '../../../interfaces';
import { cloneDeep } from '../../../util';

@Component({
  selector: 'rcc-bulk-update-form',
  changeDetection: ChangeDetectionStrategy.Default,
  templateUrl: 'bulk-update-form.component.html',
})
export class BulkUpdateFormComponent implements OnChanges {
  public buildTypes: BuildType[] = Object.keys(BUILD_TYPE_STRINGS).map(i => parseInt(i));
  languages: Language[];
  // selections
  buildTypeList: CheckListItem[] = this.buildTypes.map(type => ({
    label: this.translate.get(this.buildType(type)),
    value: type,
  }));
  appList: CheckListItem[] = [];
  // release notes (metadata)
  currentMetadata: AppMetaData;
  @Input() apps: App[];
  @Input() updateStatus: ApiRequestStatus;
  @Input() appsStatus: ApiRequestStatus;
  @Input() defaultMetaDataStatus: ApiRequestStatus;
  @Output() startBulkUpdate = new EventEmitter<BulkUpdatePayload>();

  private metadataChanged = false;

  constructor(private translate: TranslateService) {
  }

  private _defaultMetaData: AppMetaData[];

  get defaultMetaData(): AppMetaData[] {
    return this._defaultMetaData;
  }

  @Input()
  set defaultMetaData(metadata: AppMetaData[]) {
    // Ensure we're able to change this metadata in this component.
    this._defaultMetaData = cloneDeep(metadata);
  }

  private _bulkUpdateOptions: BulkUpdatePayload;

  get bulkUpdateOptions() {
    return this._bulkUpdateOptions;
  }

  @Input() set bulkUpdateOptions(value: BulkUpdatePayload) {
    this._bulkUpdateOptions = cloneDeep(value);
  }

  ngOnChanges(changes: SimpleChanges) {
    if (changes.apps || changes.defaultMetaData) {
      if (this.apps.length) {
        this.createAppCheckList();
        this.getLanguages();
        if (this.defaultMetaData.length) {
          this.createMetaData();
        }
      }
    }
  }

  createAppCheckList() {
    this.appList = this.apps.map(app => ({
      label: of(`${app.title} (${app.app_id})`),
      value: app.app_id,
    }));
  }

  getLanguages() {
    const allLanguages = new Set<string>();
    for (const app of this.apps) {
      allLanguages.add(app.main_language);
      for (const lang of app.other_languages) {
        allLanguages.add(lang);
      }
    }
    this.languages = LANGUAGES.filter(lang => allLanguages.has(lang.code))
      .sort((a, b) => a.name.localeCompare(b.name));
  }

  getLanguageName(language: string) {
    const lang = LANGUAGES.find(l => language === l.code || l.code.split('-')[ 0 ] === language);
    return lang ? lang.name : language;
  }

  getDefaultMetaData(languageCode: string) {
    languageCode = languageCode.split('-')[ 0 ];
    const metadata = this.defaultMetaData.find(m => m.language === languageCode);
    if (metadata) {
      return metadata as AppMetaData;
    }
    // Fallback to english
    return this.defaultMetaData.find(m => m.language === 'en') as AppMetaData;
  }

  createMetaData() {
    this.bulkUpdateOptions.metadata = this.languages.map(language => {
      const metadata = this.getDefaultMetaData(language.code);
      return {
        language: language.code,
        release_notes: metadata.release_notes,
      } as AppMetaData;
    });
    this.currentMetadata = this.bulkUpdateOptions.metadata[ 0 ];
  }

  getLanguageMetaData(languageCode: string): AppMetaData {
    return this.bulkUpdateOptions.metadata.find(m => m.language === languageCode) as AppMetaData;
  }

  currentMetadataChanged(text: string) {
    this.getLanguageMetaData(this.currentMetadata.language).release_notes = text;
    this.metadataChanged = true;
  }

  buildType(type: BuildType) {
    return BUILD_TYPE_STRINGS[ type ];
  }

  startBuilds() {
    // clone first, so any modification to bulkUpdateOptions here will be ok
    const options = cloneDeep(this.bulkUpdateOptions);

    if (!this.metadataChanged) {
      // keep the metadata of apps set as-is
      options.metadata = [];
    }
    this.startBulkUpdate.emit(options);
  }
}
