import { Location } from '@angular/common';
import { ChangeDetectionStrategy, Component, NgZone, ViewEncapsulation } from '@angular/core';
import { StatusBar } from '@ionic-native/status-bar/ngx';
import { AlertController, Config, Platform } from '@ionic/angular';
import { AlertOptions } from '@ionic/core';
import { Actions } from '@ngrx/effects';
import { select, Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { getScannedQr, RogerthatService } from '@oca/rogerthat';
import { CallStateType, DEFAULT_LOCALE, getLanguage, setColor } from '@oca/shared';
import { map, take } from 'rxjs/operators';


@Component({
  selector: 'cirklo-app',
  templateUrl: 'cirklo-app.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
})
export class CirkloAppComponent {
  constructor(private platform: Platform,
              private statusBar: StatusBar,
              private rogerthatService: RogerthatService,
              private translate: TranslateService,
              private actions$: Actions,
              private location: Location,
              private store: Store,
              private ngZone: NgZone,
              private config: Config,
              private alertController: AlertController) {
    this.initializeApp().catch(err => console.error(err));
  }

  async initializeApp() {
    this.translate.setDefaultLang(DEFAULT_LOCALE);
    this.platform.backButton.subscribe(async () => {
      if (await this.shouldExitApp()) {
        this.exit();
      }
    });
    await this.platform.ready();
    rogerthat.callbacks.ready(() => {
      this.ngZone.run(() => {
        this.rogerthatService.initialize();
        this.translate.use(getLanguage(rogerthat.user.language));
        if (rogerthat.system.colors) {
          setColor('primary', rogerthat.system.colors.primary);
          if (rogerthat.system.os === 'ios') {
            this.statusBar.styleDefault();
          } else {
            this.statusBar.backgroundColorByHexString(rogerthat.system.colors.primaryDark);
          }
        } else {
          this.statusBar.styleDefault();
        }
        this.isCompatible();
      });
      if (rogerthat.system.debug) {
        this.actions$.subscribe(action => {
          const { type, ...rest } = action;
          return console.log(`${type} - ${JSON.stringify(rest)}`);
        });
      }
    });
    if (this.platform.is('ios')) {
      this.translate.stream('app.cirklo.back').subscribe(translation => {
        this.config.set('backButtonText', translation);
      });
    }
  }

  private async shouldExitApp(): Promise<boolean> {
    const whitelist = [
      '/vouchers',
      '/merchants',
      '/info',
    ];
    const canExit = whitelist.includes(this.location.path());
    // When scanning a qr code, don't actually quit
    const isScanning = await this.store.pipe(
      select(getScannedQr),
      map(s => s.state === CallStateType.LOADING),
      take(1),
    ).toPromise();
    return canExit && !isScanning;
  }

  private exit() {
    rogerthat.app.exit();
  }

  private isCompatible(): boolean {
    if (!rogerthat.system.debug && !this.rogerthatService.isSupported([2, 1, 1], [2, 1, 1])) {
      const opts: AlertOptions = {
        header: this.translate.instant('app.cirklo.update_required'),
        message: this.translate.instant('app.cirklo.update_app_to_use_feat'),
        buttons: [{ role: 'cancel', text: this.translate.instant('app.cirklo.ok') }],
      };
      this.alertController.create(opts).then(alert => {
        alert.present();
        alert.onDidDismiss().then(() => this.exit());
      });
      return false;
    }
    return true;
  }

}
