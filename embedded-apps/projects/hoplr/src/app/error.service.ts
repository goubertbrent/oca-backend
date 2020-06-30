import { Injectable } from '@angular/core';
import { AlertController } from '@ionic/angular';
import { AlertOptions } from '@ionic/core';
import { Action, Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';

interface KnownError {
  message: string;
  can_retry: boolean;
}

function isKnownError(object: any): object is KnownError {
  return object.hasOwnProperty('can_retry') && object.hasOwnProperty('message');
}

@Injectable({ providedIn: 'root' })
export class ErrorService {

  constructor(private store: Store,
              private alertController: AlertController,
              private translate: TranslateService) {
  }

  // TODO might be useful to move this to shared (including error messages)
  async showErrorDialog<T extends Action>(failedAction: T, error: any) {
    const top = await this.alertController.getTop();
    if (top) {
      await top.dismiss();
    }
    const keys = ['app.hoplr.error', 'app.hoplr.close', 'app.hoplr.retry', 'app.hoplr.unknown_error'];
    this.translate.get(keys).subscribe(async translations => {
      let errorMessage: string;
      let canRetry = true;
      if (typeof error === 'string') {
        errorMessage = error;
      } else if (isKnownError(error)) {
        errorMessage = error.message;
        canRetry = error.can_retry;
        // @ts-ignore
      } else {
        errorMessage = translations[ 'app.hoplr.unknown_error' ];
      }
      const alertConfig: AlertOptions = {
        header: translations[ 'app.hoplr.error' ],
        buttons: [{
          text: translations[ 'app.hoplr.close' ],
          role: 'cancel',
        }],
      };
      if (canRetry) {
        const retryBtn = {
          text: translations[ 'app.hoplr.retry' ],
          role: 'retry',
          handler: () => {
            this.store.dispatch(failedAction as Action);
          },
        };
        // @ts-ignore
        alertConfig.buttons.push(retryBtn);
      }
      alertConfig.message = errorMessage;
      const dialog = await this.alertController.create(alertConfig);
      await dialog.present();
    });
  }
}
