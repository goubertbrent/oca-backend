import { registerLocaleData } from '@angular/common';
import localeEnGB from '@angular/common/locales/en-GB';
import localeNl from '@angular/common/locales/nl';
import { LOCALE_ID, Provider } from '@angular/core';
import { LangChangeEvent, TranslateService } from '@ngx-translate/core';
// This file assumes all embedded apps supports the same languages

// Since we have the locale files locally just register all of them
registerLocaleData(localeEnGB);
registerLocaleData(localeNl);

// en-GB to avoid the month/day/year date formatting that americans use
type SupportedLocale = 'en-GB' | 'nl';
export const DEFAULT_LOCALE = 'nl';
export const SUPPORTED_LOCALES: SupportedLocale[] = ['en-GB', 'nl'];
// Must match filenames of the files in assets/i18n
export const SUPPORTED_LANGUAGES = ['en', 'nl'];
export const DEFAULT_LANGUAGE = 'nl';

/**
 * Switches the runtime locale based on the current language
 */
export class CustomLocaleId extends String {
  currentLocale: string = DEFAULT_LOCALE;

  constructor(private translate: TranslateService) {
    super();
    translate.onLangChange.subscribe((language: LangChangeEvent) => {
      this.currentLocale = getLocaleFromLanguage(language.lang);
    });
  }

  toString(): string {
    return this.currentLocale;
  }
}

export function getLocaleFromLanguage(language: string) {
  for (const locale of SUPPORTED_LOCALES) {
    if (language.startsWith(locale)) {
      return locale;
    }
  }
  return DEFAULT_LOCALE;
}

export function getLanguage(language: string) {
  for (const locale of SUPPORTED_LANGUAGES) {
    if (language.startsWith(locale)) {
      return locale;
    }
  }
  return DEFAULT_LANGUAGE;
}

export const CUSTOM_LOCALE_PROVIDER: Provider = {
  provide: LOCALE_ID,
  useClass: CustomLocaleId,
  deps: [TranslateService],
};
