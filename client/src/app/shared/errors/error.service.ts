import { Injectable } from '@angular/core';
import { TranslateService } from '@ngx-translate/core';
import { ApiError } from './errors';

@Injectable({
  providedIn: 'root',
})
export class ErrorService {

  constructor(private translate: TranslateService) {
  }

  getErrorMessage(error: ApiError): string {
    // Translated on server
    if (error.error === 'oca.error') {
      return error.data.message;
    }
    if (this.translate.currentLang in this.translate.translations
      && error.error in this.translate.translations[ this.translate.currentLang ]) {
      return this.translate.instant(error.error, error.data);
    } else {
      return this.translate.instant('oca.error-occured-unknown-try-again');
    }
  }
}
