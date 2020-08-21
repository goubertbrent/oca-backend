import { Injectable } from '@angular/core';
import { TranslateService } from '@ngx-translate/core';
import { DialogService } from '../../../framework/client/dialog';
import { ApiError } from '../../../framework/client/rpc';
import { SERVICE_API_ERRORS } from '../constants/service-api.constants';
import { App, BulkUpdateErrors, LANGUAGES } from '../interfaces';

export interface TranslationParams {
  [ key: string ]: string;
}

@Injectable()
export class ApiErrorService {
  constructor(private dialogService: DialogService,
              private translate: TranslateService) {
  }

  /**
   * Tries its best to show a human-readable error message.
   * Uses an ApiError's `data` property as translation interpolation parameters by default.
   */
  getErrorMessage(err: ApiError | null): string {
    if (!err) {
      console.error('ApiErrorService.getErrorMessage called without error object');
      // Assuming that this is a mistake, an empty message is returned.
      return '';
    }
    let key = `rcc.${err.error}`;
    const errorData = <{ [ key: string ]: any }>err.data;
    let translationParameters: TranslationParams = { ...errorData };
    switch (err.error) {
      // Set error-specific translation parameters here
      case 'contact_linked_to_apps_error':
      case 'developer_account_linked_to_apps_error':
      case 'review_notes_linked_to_apps_error':
        translationParameters.apps = (<App[]>errorData.apps).map(app => `${app.title} (${app.app_id})`).join(', ');
        break;
      case 'validation_error':
        translationParameters.errors = '';
        // key: property that was wrong
        // value: error message (already translated by server)
        for (const [ k, message ] of Object.entries(errorData)) {
          let translatedKey: string = this.translate.instant('rcc.' + k);
          translatedKey = translatedKey.startsWith('rcc.') ? k : translatedKey;
          if (typeof message === 'string') {
            translationParameters.errors += ` ${translatedKey}: ${message}`;
          } else if (message instanceof Array) {
            // if it's an array, just combine the string values only
            const validationErrors = [];
            for (const validationError of message) {
              if (typeof validationError === 'string') {
                validationErrors.push(validationError);
              }
            }

            if (validationErrors.length) {
              translationParameters.errors += ` ${translatedKey}: ${validationErrors.join(' ')}`;
            }
          }
        }
        break;
      case 'build_missing_configurations':
        translationParameters.config_names = errorData.names.map((n: string) => this.translate.instant(`rcc.${n}`)).join(', ');
        break;
      case 'service_api_error':
        const translationKey = SERVICE_API_ERRORS[ errorData.code ];
        if (translationKey) {
          key = `rcc.${translationKey}`;
          translationParameters = errorData.fields;
        }
        break;
      case 'missing_english_translations':
        translationParameters.missing_keys = errorData.join(', ');
        break;
      case 'missing_metadata':
        key = `rcc.missing_store_listing_translations`;
        const languages = [];
        for (const code in errorData) {
          if (errorData.hasOwnProperty(code)) {
            const lowerCode = code.toLowerCase();
            const lang = LANGUAGES.find(l => l.code === lowerCode);
            if (lang) {
              languages.push(lang.name);
            }
          }
        }
        translationParameters.languages = languages.join(', ');
        break;
      case 'bulk_update_errors':
        const bulkUpdateMessages: string[] = [];
        const bulkUpdateErrors: BulkUpdateErrors = errorData.errors;
        for (const appId in bulkUpdateErrors) {
          if (bulkUpdateErrors.hasOwnProperty(appId)) {
            const errorName = bulkUpdateErrors[ appId ][ 0 ];
            const errorData1 = bulkUpdateErrors[ appId ][ 1 ];
            const m = this.getErrorMessage(<ApiError>{
              error: errorName,
              status_code: err.status_code,
              data: errorData1,
            });
            bulkUpdateMessages.push(`${appId}: ${m}`);
          }
        }
        translationParameters.errors = '\n' + bulkUpdateMessages.join('\n');
        break;
      case 'inssuficient_app_permissions':
        translationParameters.apps = errorData.apps.join(',');
        break;
    }
    let msg = this.translate.instant(key, translationParameters);
    if (msg.startsWith('rcc.')) {
      // No translation found. Fallback to the default translations based on the http status code.
      switch (err.status_code) {
        case 403:
          key = 'rcc.you_do_not_have_permission_to_view_this_information';
          break;
        default:
          key = 'rcc.unknown_error_occurred';
      }
      msg = `${this.translate.instant(key)} (${err.status_code}: ${err.error})`;
    }
    return msg;
  }

  showErrorDialog(error: ApiError | null, title = 'rcc.error', closeButton = 'rcc.close') {
    return this.dialogService.openAlert({
      title: this.translate.instant(title),
      message: this.getErrorMessage(error),
      ok: this.translate.instant(closeButton),
    });
  }
}
