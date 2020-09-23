import { InjectionToken } from '@angular/core';

/**
 * Translation keys used by this service. Must be provided via injection token.
 */
export interface ErrorServiceTranslations {
  error: string;
  knownErrorKey: string;
  unknownError: string;
  retry: string;
  close: string;
}

/** Injection token that can be used to specify translation keys used by this service. */
export const ERROR_HANDLING_TRANSLATIONS = new InjectionToken<ErrorServiceTranslations>('error-handling-translations');
