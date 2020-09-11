import { registerLocaleData } from '@angular/common';
import localeEnGB from '@angular/common/locales/en-GB';
import localeNl from '@angular/common/locales/nl';
import { LOCALE_ID, Provider } from '@angular/core';
// This file assumes all embedded apps supports the same languages

// Since we have the locale files locally just register all of them
registerLocaleData(localeEnGB);
registerLocaleData(localeNl);

export const DEFAULT_LOCALE = 'nl';
// en-GB to avoid the month/day/year date formatting that americans use
export const SUPPORTED_LOCALES: string[] = ['en-GB', 'nl'];
// Must match filenames of the files in assets/i18n
export const SUPPORTED_LANGUAGES = ['en', 'nl'];
export const DEFAULT_LANGUAGE = 'nl';

export function getLocaleFromLanguage(language: string) {
  language = language.replace('_', '-');
  const split = language.split('-');
  for (const locale of SUPPORTED_LOCALES) {
    if (locale.startsWith(language) || split[ 0 ] === locale.split('-')[ 0 ]) {
      return locale;
    }
  }
  return DEFAULT_LOCALE;
}

export function getLanguage(language: string) {
  language = language.replace('_', '-')
  const split = language.split('-');
  for (const lang of SUPPORTED_LANGUAGES) {
    if (lang.startsWith(language) || split[ 0 ] === language) {
      return lang;
    }
  }
  return DEFAULT_LANGUAGE;
}

function getLocale() {
  if (SUPPORTED_LOCALES.includes(navigator.language)) {
    return navigator.language;
  }
  return DEFAULT_LOCALE;
}

export const CUSTOM_LOCALE_PROVIDER: Provider = {
  provide: LOCALE_ID,
  useFactory: getLocale,
};
