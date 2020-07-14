import { Injectable } from '@angular/core';
import { AlertController } from '@ionic/angular';
import { AlertOptions } from '@ionic/core';
import { Action, Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';


@Injectable({ providedIn: 'root' })
export class ErrorService {

  constructor(private store: Store,
              private alertController: AlertController,
              private translate: TranslateService) {
  }

  // TODO might be useful to move this to shared (including error messages)
  async showErrorDialog<T extends Action>(failedAction: T, error: any) {
    const top = await this.alertController.getTop();
    if (error instanceof Error) {
      console.error(error);
    }
    if (top) {
      await top.dismiss();
    }
    const keys = ['app.trash.error', 'app.trash.close', 'app.trash.retry', 'app.trash.unknown_error'];
    this.translate.get(keys).subscribe(async translations => {
      let errorMessage: string;
      if (typeof error === 'string') {
        errorMessage = error;
      } else {
        errorMessage = translations[ 'app.trash.unknown_error' ];
      }
      const alertConfig: AlertOptions = {
        header: translations[ 'app.trash.error' ],
        buttons: [{
          text: translations[ 'app.trash.close' ],
          role: 'cancel',
        }],
      };
      const retryBtn = {
        text: translations[ 'app.trash.retry' ],
        role: 'retry',
        handler: () => {
          this.store.dispatch(failedAction as Action);
        },
      };
      // @ts-ignore
      alertConfig.buttons.push(retryBtn);
      alertConfig.message = errorMessage;
      const dialog = await this.alertController.create(alertConfig);
      await dialog.present();
    });
  }
}
