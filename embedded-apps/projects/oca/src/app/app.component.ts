import { Location } from '@angular/common';
import { ChangeDetectionStrategy, Component, NgZone, ViewEncapsulation } from '@angular/core';
import { Router } from '@angular/router';
import { StatusBar } from '@ionic-native/status-bar/ngx';
import { AlertController, Platform } from '@ionic/angular';
import { AlertOptions } from '@ionic/core';
import { Actions } from '@ngrx/effects';
import { TranslateService } from '@ngx-translate/core';
import { RogerthatService } from '@oca/rogerthat';
import { DEFAULT_LANGUAGE, getLanguage, setColor } from '@oca/shared';


@Component({
  selector: 'app-root',
  templateUrl: 'app.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
})
export class AppComponent {
  constructor(private platform: Platform,
              private statusBar: StatusBar,
              private rogerthatService: RogerthatService,
              private translate: TranslateService,
              private actions$: Actions,
              private router: Router,
              private location: Location,
              private ngZone: NgZone,
              private alertController: AlertController) {
    this.initializeApp().catch(err => console.error(err));
  }

  async initializeApp() {
    this.translate.setDefaultLang(DEFAULT_LANGUAGE);
    await this.platform.ready();
    this.platform.backButton.subscribe(async () => {
      if (this.shouldExitApp()) {
        this.exit();
      }
    });
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
        if (this.isCompatible() && ['', '/'].includes(this.location.path())) {
          this.router.navigate(this.getRootPage());
        }
      });
    });
    // this.actions$.subscribe(action => {
    //   const { type, ...rest } = action;
    //   return console.log(`${type} - ${JSON.stringify(rest)}`);
    // });
  }

  private shouldExitApp(): boolean {
    const whitelist = [
      '/q-matic/appointments',
      '/jcc-appointments/appointments',
      '/events',
    ];
    return whitelist.includes(this.location.path());
  }

  private getRootPage(): string[] {
    const TAGS = {
      Q_MATIC: sha256('__sln__.q_matic'),
      EVENTS: sha256('agenda'),
      JCC_APPOINTMENTS: sha256('__sln__.jcc_appointments'),
    };
    const PAGE_MAPPING = {
      [ TAGS.Q_MATIC ]: ['q-matic'],
      [ TAGS.EVENTS ]: ['events'],
      [ TAGS.JCC_APPOINTMENTS ]: ['jcc-appointments'],
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
