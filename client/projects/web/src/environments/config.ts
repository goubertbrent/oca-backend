import { Provider } from '@angular/core';
import { ERROR_HANDLING_TRANSLATIONS, ErrorServiceTranslations } from '@oca/web-shared';

// TODO correct translations
export const ERROR_HANDLING_TRANLATIONS_PROVIDER: Provider = {
  provide: ERROR_HANDLING_TRANSLATIONS,
  useValue: {
    error: 'web.Error',
    knownErrorKey: 'web.translated-error',
    unknownError: 'web.error-occured-unknown-try-again',
    retry: 'web.Retry',
    close: 'web.Close',
  } as ErrorServiceTranslations,
};
