import { ChangeDetectionStrategy, ChangeDetectorRef, Component, EventEmitter, Input, OnDestroy, Output } from '@angular/core';
import { FormBuilder, FormControl, FormGroup, Validators } from '@angular/forms';
import { MatDialog } from '@angular/material/dialog';
import { SimpleDialogComponent, SimpleDialogData, SimpleDialogResult } from '@oca/web-shared';
import { IFormArray, IFormBuilder, IFormGroup } from '@rxweb/types';
import { Observable, ReplaySubject, Subject } from 'rxjs';
import { debounceTime, filter, map, takeUntil } from 'rxjs/operators';
import { iconValidator } from '../../../constants';
import { EmbeddedApp, Language, LANGUAGES } from '../../../interfaces';
import {
  AddTranslationDialogComponent,
  AddTranslationDialogData,
  AddTranslationDialogResult,
} from '../add-translation-dialog/add-translation-dialog.component';
import { HomeScreenService } from '../home-screen.service';
import {
  BottomSheetListItemTemplate,
  BottomSheetListItemType,
  BottomSheetSectionTemplate,
  HomeScreenDefaultTranslation,
  HomeScreenSectionType,
  TranslationInternal,
  TranslationValue,
} from '../homescreen';
import {
  HomeScreen,
  HomeScreenBottomNavigation,
  HomeScreenBottomSheet,
  HomeScreenBottomSheetHeader,
  HomeScreenContent,
  HomeScreenContentTypeEnum,
  HomeScreenNavigationButton,
} from '../models';

const TRANSLATION_PREFIX = '$';

@Component({
  selector: 'rcc-home-screen-form',
  templateUrl: './home-screen-form.component.html',
  styleUrls: ['./home-screen-form.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class HomeScreenFormComponent implements OnDestroy {
  LANGUAGES = LANGUAGES;
  HomeScreenContentTypeEnum = HomeScreenContentTypeEnum;
  homeScreenTypes = [
    { type: HomeScreenContentTypeEnum.Native, label: 'Native' },
    { type: HomeScreenContentTypeEnum.EmbeddedApp, label: 'Embedded app' },
  ];
  // Default language translations array
  translations$: ReplaySubject<TranslationInternal[]> = new ReplaySubject();
  // Default language translations mapping (includes prefix)
  translationsMapping: TranslationValue = {};
  languages$: ReplaySubject<Language[]> = new ReplaySubject();

  // Translations
  newLanguageControl = new FormControl();
  filteredLanguages$: Observable<Language[]>;

  homeScreenFormGroup: IFormGroup<HomeScreen>;

  @Input() embeddedApps: EmbeddedApp[];
  @Input() defaultTranslations: HomeScreenDefaultTranslation[];
  @Output() saved = new EventEmitter<HomeScreen>();
  private formBuilder: IFormBuilder;
  private destroyed$ = new Subject();
  private initialized = false;

  constructor(formBuilder: FormBuilder,
              private changeDetectorRef: ChangeDetectorRef,
              private matDialog: MatDialog,
              private homeScreenFormsService: HomeScreenService) {
    this.formBuilder = formBuilder;
    this.homeScreenFormGroup = this.formBuilder.group<HomeScreen>(
      {
        version: this.formBuilder.control(1),
        bottom_navigation: this.formBuilder.group<HomeScreenBottomNavigation>({
          buttons: this.formBuilder.array<HomeScreenNavigationButton>([]),
        }),
        bottom_sheet: this.formBuilder.group<HomeScreenBottomSheet>({
          header: this.formBuilder.group<HomeScreenBottomSheetHeader>({
            image: this.formBuilder.control<string | null>(null),
            subtitle: this.formBuilder.control<string | null>(null),
            title: this.formBuilder.control<string>(''),
          }),
          rows: this.formBuilder.array([]),
        }),
        content: this.formBuilder.group<HomeScreenContent>({
          embedded_app: this.formBuilder.control(null),
          service_email: this.formBuilder.control(null, Validators.email),
          type: this.formBuilder.control(HomeScreenContentTypeEnum.EmbeddedApp),
        }),
        default_language: this.formBuilder.control('en'),
        translations: this.formBuilder.group<HomeScreen['translations']>({}),
      },
    );
    const content = this.homeScreenFormGroup.controls.content as IFormGroup<HomeScreenContent>;
    content.controls.type.valueChanges.pipe(takeUntil(this.destroyed$)).subscribe(type => {
      if (type === HomeScreenContentTypeEnum.EmbeddedApp) {
        content.controls.embedded_app!!.setValidators([Validators.required]);
      } else {
        content.controls.embedded_app!!.clearValidators();
      }
    });
    this.homeScreenFormGroup.valueChanges.pipe(
      // buttonsFormArray.clear and buttonsFormArray.push triggers valueChanges, so skip these events until we've created all controls
      filter(() => this.initialized && this.homeScreenFormGroup.valid),
      takeUntil(this.destroyed$),
      debounceTime(500),
      filter(() => this.homeScreenFormGroup.valid),
    ).subscribe(value => this.saved.emit(value!!));
    this.filteredLanguages$ = this.newLanguageControl.valueChanges.pipe(
      map(input => {
        const re = new RegExp(input ?? '', 'i');
        if (input) {
          return LANGUAGES.filter(l => input.includes(l.code) || l.name.match(re)).slice(0, 10);
        } else {
          return LANGUAGES;
        }
      }),
    );
  }

  @Input() set homeScreen(value: HomeScreen) {
    this.initialized = false;
    const bottom = this.homeScreenFormGroup.controls.bottom_navigation as IFormGroup<HomeScreenBottomNavigation>;
    const buttonsFormArray = bottom.controls.buttons as IFormArray<HomeScreenNavigationButton>;
    buttonsFormArray.clear();
    if (value.bottom_navigation.buttons) {
      for (const btn of value.bottom_navigation.buttons) {
        buttonsFormArray.push(this.getNavigationButtonFormGroup(btn));
      }
    }
    const translationsFormGroup = this.homeScreenFormGroup.controls.translations as FormGroup;
    for (const language of Object.keys(translationsFormGroup.controls)) {
      translationsFormGroup.removeControl(language);
    }
    for (const [lang, translations] of Object.entries(value.translations)) {
      translationsFormGroup.addControl(lang, this.getTranslationsFormGroup(translations));
    }
    const bottomSheet = this.homeScreenFormGroup.controls.bottom_sheet as IFormGroup<HomeScreenBottomSheet>;
    const rows = bottomSheet.controls.rows as unknown as IFormArray<BottomSheetSectionTemplate>;
    rows.clear();
    for (const row of value.bottom_sheet.rows) {
      rows.push(this.homeScreenFormsService.getHomeScreenItemForm(row as unknown as BottomSheetSectionTemplate));
    }
    this.homeScreenFormGroup.patchValue(value, { emitEvent: false });
    this.initialized = true;
    this.setLanguages(value);
  }

  ngOnDestroy() {
    this.destroyed$.next();
    this.destroyed$.complete();
  }

  removeLanguage(language: Language) {
    const data: SimpleDialogData = {
      title: 'Delete language',
      message: `Are you sure you want to remove the language ${language.name}?`,
      ok: 'Yes',
      cancel: 'No',
    };
    this.matDialog.open<SimpleDialogComponent, SimpleDialogData, SimpleDialogResult>(SimpleDialogComponent, { data })
      .afterClosed().subscribe(result => {
      if (result?.submitted) {
        (this.homeScreenFormGroup.controls.translations as IFormGroup<HomeScreen['translations']>).removeControl(language.code);
        const { translations, default_language } = this.homeScreenFormGroup.value!!;
        this.setTranslations(translations, default_language);
      }
    });
  }

  removeTranslation(translation: TranslationInternal) {
    const errors = this.findTranslationUsage(this.homeScreenFormGroup.value!!, translation);
    if (errors.length) {
      const data: SimpleDialogData = {
        ok: 'Ok',
        title: 'Error',
        message: ['This translation is still used by:', ...errors].join('\n - '),
      };
      this.matDialog.open<SimpleDialogComponent, SimpleDialogData, SimpleDialogResult>(SimpleDialogComponent, { data });
    } else {
      const translationsFormGroup = this.homeScreenFormGroup.controls.translations as IFormGroup<HomeScreen['translations']>;
      for (const formGroup of Object.values(translationsFormGroup.controls)) {
        (formGroup as IFormGroup<TranslationValue>).removeControl(translation.key);
      }
      const { translations, default_language } = this.homeScreenFormGroup.value!!;
      this.setTranslations(translations, default_language);
    }
  }

  addLanguage(languageCode: string, input: HTMLInputElement) {
    const language = LANGUAGES.find(l => l.code === languageCode);
    const homeScreen = this.homeScreenFormGroup.value!!;
    const translations = homeScreen.translations;
    if (language && !(languageCode in translations)) {
      const newTranslations = { ...translations[ homeScreen.default_language ] };
      const defaultTranslationsMapping = this.getDefaultTranslationMapping(languageCode);
      // Try to prefill with default translations, otherwise set to empty string
      for (const key of Object.keys(newTranslations)) {
        newTranslations[ key ] = defaultTranslationsMapping.get(key) ?? '';
      }
      const group = this.getTranslationsFormGroup(newTranslations);
      (this.homeScreenFormGroup.controls.translations as FormGroup).addControl(languageCode, group);
    }
    this.setLanguages(this.homeScreenFormGroup.value!!);
    this.newLanguageControl.reset('');
    // for some reason the input isn't reset by above line... manually reset it
    input.value = '';
  }

  addTranslation() {
    const defaultLang = this.homeScreenFormGroup.value!!.default_language;
    const data = {
      defaultLanguage: LANGUAGES.find(l => l.code === defaultLang)!!,
      // Only return the default translations that aren't already present in the current translations
      defaultTranslations: this.defaultTranslations.filter(t => !(`${TRANSLATION_PREFIX}${t.key}` in this.translationsMapping)),
    };
    this.matDialog.open<AddTranslationDialogComponent, AddTranslationDialogData,
      AddTranslationDialogResult>(AddTranslationDialogComponent, { data }).afterClosed().subscribe(result => {
      const translations = this.homeScreenFormGroup.controls.translations as IFormGroup<HomeScreen['translations']>;
      if (result) {
        for (const [language, formGroup] of Object.entries(translations.controls)) {
          const defaultMapping = this.getDefaultTranslationMapping(language);
          const translation = language === defaultLang ? result.value : defaultMapping.get(result.key) ?? '';
          const newFormGroup = new FormControl(translation, Validators.required);
          (formGroup as IFormGroup<TranslationValue>).addControl(result.key, newFormGroup);
        }
        this.setTranslations(this.homeScreenFormGroup.value!!.translations, defaultLang);
      }
    });
  }

  private findTranslationUsage(homeScreen: HomeScreen, translation: TranslationInternal): string[] {
    const errors: string[] = [];
    const keyToDelete = translation.prefixedKey;
    const header = homeScreen.bottom_sheet.header;
    if (header.title === keyToDelete || header.subtitle === keyToDelete) {
      errors.push('Bottom sheet header');
    }
    for (let rowNum = 0; rowNum < homeScreen.bottom_sheet.rows.length; rowNum++) {
      const row = homeScreen.bottom_sheet.rows[ rowNum ] as unknown as BottomSheetSectionTemplate;
      switch (row.type) {
        case HomeScreenSectionType.TEXT:
          if (row.title === keyToDelete || row.description === keyToDelete) {
            errors.push(`Bottom sheet row ${rowNum + 1} description`);
          }
          break;
        case HomeScreenSectionType.LIST:
          for (let listNum = 0; listNum < row.items.length; listNum++) {
            const item = row.items[ listNum ];
            switch (item.type) {
              case BottomSheetListItemType.OPENING_HOURS:
                break;
              case BottomSheetListItemType.EXPANDABLE:
              case BottomSheetListItemType.LINK:
                if (item.title === keyToDelete) {
                  errors.push(`Bottom sheet row ${rowNum + 1}, item ${listNum + 1}`);
                }
                break;
            }
          }
          break;
        case HomeScreenSectionType.NEWS:
          break;
      }
    }
    if (homeScreen.bottom_navigation?.buttons) {
      for (let i = 0; i < homeScreen.bottom_navigation.buttons.length; i++) {
        const button = homeScreen.bottom_navigation.buttons[ i ];
        if (button.label === keyToDelete) {
          errors.push(`Bottom navigation button ${i + 1}`);
        }
      }
    }
    return errors;
  }

  private setLanguages(homeScreen: HomeScreen) {
    this.languages$.next(LANGUAGES.filter(l => l.code in homeScreen.translations));
    this.setTranslations(homeScreen.translations, homeScreen.default_language);
  }

  private setTranslations(translations: HomeScreen['translations'], defaultLanguage: string) {
    const array = Object.entries(translations[ defaultLanguage ])
      .map(([key, value]) => ({ key, value, prefixedKey: `${TRANSLATION_PREFIX}${key}` }))
      .sort((first, second) => first.value.localeCompare(second.value));
    this.translations$.next(array);
    this.translationsMapping = array.reduce((acc, translation) => {
      acc[ translation.prefixedKey ] = translation.value;
      return acc;
    }, {} as TranslationValue);
  }

  private getTranslationsFormGroup(translations: { [ key: string ]: string }) {
    const translationKeys = Object.keys(translations);
    const controls = Object.fromEntries(translationKeys.map(key => {
      return [key, this.formBuilder.control(translations[ key ], Validators.required)];
    }));
    return this.formBuilder.group<TranslationValue>(controls);
  }

  private getNavigationButtonFormGroup(navButton: HomeScreenNavigationButton) {
    return this.formBuilder.group<HomeScreenNavigationButton>({
      label: this.formBuilder.control(navButton.label, Validators.required),
      action: this.formBuilder.control(navButton.action, Validators.required),
      icon: this.formBuilder.control(navButton.icon, [Validators.required, iconValidator]),
    });
  }

  private getDefaultTranslationMapping(languageCode: string) {
    const mapping = new Map<string, string>();
    for (const trans of this.defaultTranslations) {
      if (languageCode in trans.values) {
        mapping.set(trans.key, trans.values[ languageCode ]);
      }
    }
    return mapping;
  }
}

