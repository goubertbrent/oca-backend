import { CollectionViewer, DataSource } from '@angular/cdk/collections';
import { ChangeDetectionStrategy, Component, ElementRef, Input, OnInit, ViewChild } from '@angular/core';
import { AbstractControl } from '@angular/forms';
import { BehaviorSubject, Observable } from 'rxjs';
import { Language, LANGUAGES, NameValue, Translations } from '../../../interfaces';
import { AbstractControlValueAccessor, makeNgModelProvider } from '../../../util';

export class TranslationsDatabase {
  dataChange: BehaviorSubject<NameValue[]> = new BehaviorSubject<NameValue[]>([]);

  private _language: string | null = null;

  get language() {
    return this._language;
  }

  get data(): NameValue[] {
    return this.dataChange.value;
  }

  setTranslations(translations: NameValue[], language: string) {
    this._language = language;
    this.dataChange.next(translations);
  }

  addTranslation(translation: NameValue) {
    this.dataChange.next(this.data.concat(translation));
  }

  removeTranslation(translation: NameValue) {
    this.dataChange.next(this.data.filter(t => t.name !== translation.name));
  }

  hasTranslation(translation: NameValue): boolean {
    return this.data.some(t => translation.name === name);
  }
}

export class TranslationsDataSource extends DataSource<NameValue> {
  constructor(private translationsDatabase: TranslationsDatabase) {
    super();
  }

  connect(collectionViewer: CollectionViewer): Observable<NameValue[]> {
    return this.translationsDatabase.dataChange;
  }

  disconnect(collectionViewer: CollectionViewer): void {
    // no-op
  }
}

@Component({
  selector: 'rcc-translations-editor',
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: 'translations-editor.component.html',
  providers: [ makeNgModelProvider(TranslationsEditorComponent) ],
})
export class TranslationsEditorComponent extends AbstractControlValueAccessor implements OnInit {
  @Input() allowedLanguages: string[];
  @Input() defaultLanguage: string;
  @ViewChild('nameInput', { static: false }) nameInput: ElementRef;
  @ViewChild('translationKey', { static: false }) translationKey: AbstractControl;
  @ViewChild('translationValue', { static: false }) translationValue: AbstractControl;

  selectedLang: Language;
  newTranslation: NameValue;
  translationsDatabase = new TranslationsDatabase();
  dataSource: TranslationsDataSource;
  displayedColumns = [ 'name', 'value', 'remove' ];

  get translations(): Translations {
    return this.value;
  }

  set translations(value: Translations) {
    this.value = value; // From AbstractControlValueAccessor
  }

  private _languages: Language[];

  get languages(): Language[] {
    if (this._languages) {
      return this._languages;
    }
    if (!this.allowedLanguages) {
      return LANGUAGES;
    }
    this._languages = LANGUAGES.filter(l => this.allowedLanguages.includes(l.code));
    return this._languages;
  }

  public ngOnInit(): void {
    this.newTranslation = {
      name: '',
      value: '',
    };
    this.dataSource = new TranslationsDataSource(this.translationsDatabase);
  }

  trackByCode(index: number, item: Language) {
    return item.code;
  }

  trackByName(index: number, item: NameValue) {
    return item.name;
  }

  removeTranslation(translation: NameValue) {
    this.translationsDatabase.removeTranslation(translation);
    this._setTranslations();
  }

  languageChanged() {
    this._setTranslations();
    this.translationsDatabase.setTranslations(this._getTranslations(), this.selectedLang.code);
  }

  addTranslation() {
    if (!this.translationKey.valid || !this.translationValue.valid) {
      return;
    }
    this.newTranslation = {
      name: this.newTranslation.name.trim(),
      value: this.newTranslation.value.trim(),
    };
    if (!this.newTranslation.name || !this.newTranslation.value
      || this.translationsDatabase.hasTranslation(this.newTranslation)) {
      return;
    }
    this.translationsDatabase.addTranslation(this.newTranslation);
    this._setTranslations();
    this.newTranslation = {
      name: '',
      value: '',
    };
    this.nameInput.nativeElement.focus();
  }

  private _getTranslations() {
    const trans = this.translations[ this.selectedLang.code ];
    if (!trans) {
      this.translations[ this.selectedLang.code ] = [];
    }
    return this.translations[ this.selectedLang.code ];
  }

  private _setTranslations() {
    if (this.translationsDatabase.language) {
      this.translations = {
        ...this.translations,
        [ this.translationsDatabase.language ]: this.translationsDatabase.data,
      };
    }
  }
}
