import { Provider } from '@angular/core';
import { ErrorServiceTranslations, ERROR_HANDLING_TRANSLATIONS } from '@oca/web-shared';
import { Options } from 'easymde';

export const googleMapsKey = 'AIzaSyAPesOjDo8VzgaUeAsc4Od-GoBBO11vQZE';

export const EASYMDE_OPTIONS = {
  autoDownloadFontAwesome: false,
  spellChecker: false,
  status: false,
  toolbar: ['bold', 'italic', 'strikethrough', 'unordered-list', 'link'] as any,
} as Options;

export const ERROR_HANDLING_TRANLATIONS_PROVIDER: Provider = {
  provide: ERROR_HANDLING_TRANSLATIONS,
  useValue: {
    error: 'oca.Error',
    knownErrorKey: 'oca.error',
    unknownError: 'oca.error-occured-unknown-try-again',
    retry: 'oca.Retry',
    close: 'oca.Close',
  } as ErrorServiceTranslations,
};
