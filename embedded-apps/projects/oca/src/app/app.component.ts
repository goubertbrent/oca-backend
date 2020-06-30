import { Location } from '@angular/common';
import { ChangeDetectionStrategy, ChangeDetectorRef, Component, ViewEncapsulation } from '@angular/core';
import { Router } from '@angular/router';
import { SplashScreen } from '@ionic-native/splash-screen/ngx';
import { StatusBar } from '@ionic-native/status-bar/ngx';
import { AlertController, Platform } from '@ionic/angular';
import { AlertOptions } from '@ionic/core';
import { Actions } from '@ngrx/effects';
import { select, Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { getScannedQr, RogerthatService } from '@oca/rogerthat';
import { CallStateType, DEFAULT_LOCALE, getLanguage, setColor } from '@oca/shared';
import { map, take } from 'rxjs/operators';


@Component({
  selector: 'app-root',
  templateUrl: 'app.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
})
export class AppComponent {
  constructor(private platform: Platform,
              private splashScreen: SplashScreen,
              private statusBar: StatusBar,
              private rogerthatService: RogerthatService,
              private translate: TranslateService,
              private cdRef: ChangeDetectorRef,
              private actions$: Actions,
              private router: Router,
              private location: Location,
              private store: Store,
              private alertController: AlertController) {
    this.initializeApp();
  }

  async initializeApp() {
    this.translate.setDefaultLang(DEFAULT_LOCALE);
    await this.platform.ready();
    this.splashScreen.hide();
    this.platform.backButton.subscribe(async () => {
      if (await this.shouldExitApp()) {
        this.exit();
      }
    });
    rogerthat.callbacks.ready(() => {
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
      this.rogerthatService.initialize();
      if (this.isCompatible() && ['', '/'].includes(this.location.path())) {
        this.router.navigate(this.getRootPage());
      }
    });
    // this.actions$.subscribe(action => {
    //   const { type, ...rest } = action;
    //   return console.log(`${type} - ${JSON.stringify(rest)}`);
    // });
  }

  private async shouldExitApp(): Promise<boolean> {
    const whitelist = [
      '/q-matic/appointments',
      '/jcc-appointments/appointments',
      '/events',
      '/cirklo/vouchers',
      '/cirklo/merchants',
      '/cirklo/info',
    ];
    const canExit = whitelist.includes(this.router.url);
    // When scanning a qr code, don't actually quit
    const isScanning = await this.store.pipe(
      select(getScannedQr),
      map(s => s.state === CallStateType.LOADING),
      take(1),
    ).toPromise();
    return canExit && !isScanning;
  }

  private getRootPage(): string[] {
    const TAGS = {
      Q_MATIC: sha256('__sln__.q_matic'),
      EVENTS: sha256('agenda'),
      JCC_APPOINTMENTS: sha256('__sln__.jcc_appointments'),
      CIRKLO: sha256('__sln__.cirklo'),
    };
    const PAGE_MAPPING = {
      [ TAGS.Q_MATIC ]: ['q-matic'],
      [ TAGS.EVENTS ]: ['events'],
      [ TAGS.JCC_APPOINTMENTS ]: ['jcc-appointments'],
      [ TAGS.CIRKLO ]: ['cirklo'],
    };
    const tag = rogerthat.menuItem.hashedTag in PAGE_MAPPING ? rogerthat.menuItem.hashedTag : TAGS.EVENTS;
    return PAGE_MAPPING[ tag ];
  }

  private exit() {
    rogerthat.app.exit();
  }

  private isCompatible(): boolean {
    if (!rogerthat.system.debug && !this.rogerthatService.isSupported([2, 1, 1], [2, 1, 1])) {
      const opts: AlertOptions = {
        header: this.translate.instant('app.oca.update_required'),
        message: this.translate.instant('app.oca.update_app_to_use_feat'),
        buttons: [{ role: 'cancel', text: this.translate.instant('app.oca.ok') }],
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
