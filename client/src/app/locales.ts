import { registerLocaleData } from '@angular/common';
import { LOCALE_ID, Provider } from '@angular/core';
import { LangChangeEvent, TranslateService } from '@ngx-translate/core';

type SupportedLocale = 'en' | 'nl' | 'fr';
const DEFAULT_LOCALE = 'en';
const SUPPORTED_LOCALES: SupportedLocale[] = ['en', 'nl', 'fr'];

/**
 * Switches the runtime locale based on the current language
 */
export class CustomLocaleId extends String {
  currentLocale: string = DEFAULT_LOCALE;

  constructor(private translate: TranslateService) {
    super();
    translate.onLangChange.subscribe((language: LangChangeEvent) => {
      const newLocale = this.getLocaleFromLanguage(language.lang);
      getLocaleModule(newLocale as SupportedLocale).then(mod => {
        this.currentLocale = newLocale;
        registerLocaleData(mod.default);
      });
    });
  }

  toString(): string {
    return this.currentLocale;
  }

  private getLocaleFromLanguage(language: string) {
    for (const locale of SUPPORTED_LOCALES) {
      if (language.startsWith(locale)) {
        return locale;
      }
    }
    return DEFAULT_LOCALE;
  }
}

function getLocaleModule(language: SupportedLocale) {
  switch (language) {
    case 'nl':
      return import('@angular/common/locales/nl');
    case 'fr':
      return import('@angular/common/locales/fr');
    case 'en':
      return import('@angular/common/locales/en');
  }
}

export const CUSTOM_LOCALE_PROVIDER: Provider = {
  provide: LOCALE_ID,
  useClass: CustomLocaleId,
  deps: [TranslateService],
};
