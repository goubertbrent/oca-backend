import { Injectable } from '@angular/core';
import { AlertController } from '@ionic/angular';
import { Action, Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { AppState } from '../reducers';

@Injectable({ providedIn: 'root' })
export class ErrorService {

  constructor(private store: Store<AppState>,
              private alertController: AlertController,
              private translate: TranslateService) {
  }


  async showErrorDialog<T extends Action>(failedAction: T, error: any) {
    let errorMessage: string;
    if (typeof error === 'string') {
      errorMessage = error;
    } else {
      errorMessage = this.translate.instant('app.oca.unknown_error');
    }
    const top = await this.alertController.getTop();
    if (top) {
      await top.dismiss();
    }
    const dialog = await this.alertController.create({
      header: this.translate.instant('app.oca.error'),
      message: errorMessage,
      buttons: [
        {
          text: this.translate.instant('app.oca.close'),
          role: 'cancel',
        },
        {
          text: this.translate.instant('app.oca.retry'),
          handler: () => {
            this.store.dispatch(failedAction as Action);
          },
        },
      ],
    });
    await dialog.present();
  }
}
