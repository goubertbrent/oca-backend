import { ChangeDetectionStrategy, Component, EventEmitter, Input, OnChanges, OnInit, Output, SimpleChanges } from '@angular/core';
import { FormControl } from '@angular/forms';
import { MatChipInputEvent } from '@angular/material/chips';
import { Observable } from 'rxjs';
import { map, startWith } from 'rxjs/operators';
import { ApiRequestStatus } from '../../../../../framework/client/rpc';
import {
  App,
  APP_STORE_CATEGORIES,
  Contact,
  DeveloperAccount,
  Language,
  LANGUAGES,
  PLAY_STORE_CATEGORIES,
  ReviewNotes,
} from '../../../interfaces';

@Component({
  selector: 'rcc-store-listing-detail-form',
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: 'store-listing-detail-form.component.html',
})
export class StoreListingDetailFormComponent implements OnInit, OnChanges {
  languageFormControl = new FormControl();
  languages = LANGUAGES;
  appStoreCategories = APP_STORE_CATEGORIES;
  playStoreCategories = PLAY_STORE_CATEGORIES;
  filteredLanguages: Observable<Language[]>;
  androidDeveloperAccounts: DeveloperAccount[] = [];
  iosDeveloperAccounts: DeveloperAccount[] = [];

  @Input() updateAppStatus: ApiRequestStatus;
  @Input() reviewNotes: ReviewNotes[];
  @Input() contacts: Contact[];
  @Input() developerAccounts: DeveloperAccount[];
  @Output() save = new EventEmitter<App>();

  private _app: App;

  get app() {
    return this._app;
  }

  @Input()
  set app(app: App) {
    this._app = { ...app };
  }

  ngOnInit() {
    this.filteredLanguages = this.languageFormControl.valueChanges.pipe(
      startWith(''),
      map(val => val ? this.filterLanguages(val) : [ ...LANGUAGES ]),
    );
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes.developerAccounts && changes.developerAccounts.currentValue) {
      const devAccounts = <DeveloperAccount[]>changes.developerAccounts.currentValue;
      this.androidDeveloperAccounts = devAccounts.filter(d => d.type === 'android');
      this.iosDeveloperAccounts = devAccounts.filter(d => d.type === 'ios');
    }
  }

  getLanguage(langCode: string) {
    const lang = LANGUAGES.find(l => l.code === langCode);
    return lang ? lang.name : null;
  }

  addLocale(event: MatChipInputEvent) {
    if (!this.app.other_languages.includes(event.value) && !this.isMainLanguage(event.value) && this.getLanguage(event.value)) {
      this.app.other_languages = [ ...<string[]>this.app.other_languages, event.value ];
    }
    this.languageFormControl.reset();
  }

  removeLanguage(langCode: string) {
    this.app.other_languages = (<string[]>this.app.other_languages).filter(lang => lang !== langCode);
  }

  submit() {
    this.save.emit({ ...this.app });
  }

  private isMainLanguage(lang: string) {
    return this.app.main_language === lang;
  }

  private filterLanguages(val: string): Language[] {
    const re = new RegExp(val, 'gi');
    return LANGUAGES.filter(lang => !this.isMainLanguage(lang.code) && (re.test(lang.name) || re.test(lang.code)));
  }
}
