import { registerLocaleData } from '@angular/common';
import localeEnGB from '@angular/common/locales/en-GB';
import localeNl from '@angular/common/locales/nl';
import { LOCALE_ID, Provider } from '@angular/core';
// This file assumes all embedded apps supports the same languages

// Since we have the locale files locally just register all of them
registerLocaleData(localeEnGB);
registerLocaleData(localeNl);

export const DEFAULT_LOCALE = 'en-GB';
// en-GB first to avoid US formatting in non US countries
export const SUPPORTED_LOCALES: string[] = ['en-GB', 'en-US', 'nl'];
// Must match filenames of the files in assets/i18n for *all* embedded apps
export const SUPPORTED_LANGUAGES = ['en', 'nl'];
export const DEFAULT_LANGUAGE = 'en';

export function getLanguage(language: string) {
  language = language.replace('_', '-');
  const split = language.split('-');
  for (const lang of SUPPORTED_LANGUAGES) {
    if (lang.startsWith(language) || split[ 0 ] === lang) {
      return lang;
    }
  }
  return DEFAULT_LANGUAGE;
}

function getLocale() {
  const userLocale = navigator.language.replace('_', '-');
  if (SUPPORTED_LOCALES.includes(userLocale)) {
    return userLocale;
  }
  const language = userLocale.split('-')[ 0 ];
  for (const locale of SUPPORTED_LOCALES) {
    if (locale.startsWith(language)) {
      return locale;
    }
  }
  return DEFAULT_LOCALE;
}

export const CUSTOM_LOCALE_PROVIDER: Provider = {
  provide: LOCALE_ID,
  useFactory: getLocale,
};
