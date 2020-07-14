import { Location } from '@angular/common';
import { ChangeDetectionStrategy, ChangeDetectorRef, Component, NgZone, ViewEncapsulation } from '@angular/core';
import { Router } from '@angular/router';
import { SplashScreen } from '@ionic-native/splash-screen/ngx';
import { StatusBar } from '@ionic-native/status-bar/ngx';
import { Platform } from '@ionic/angular';
import { Actions } from '@ngrx/effects';
import { TranslateService } from '@ngx-translate/core';
import { RogerthatService } from '@oca/rogerthat';
import { DEFAULT_LOCALE, getLanguage } from '@oca/shared';


@Component({
  selector: 'trash-root',
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
              private ngZone: NgZone,
              private actions$: Actions,
              private location: Location,
              private router: Router) {
    this.initializeApp();
  }

  initializeApp() {
    this.translate.setDefaultLang(DEFAULT_LOCALE);
    this.platform.ready().then(() => {
      // @ts-ignore
      const hasCordova = typeof cordova !== 'undefined';
      if (hasCordova) {
        this.splashScreen.hide();
        this.platform.backButton.subscribe(() => {
          if (this.shouldExitApp()) {
            this.exit();
          }
        });
      }
      if (rogerthat.system.debug) {
        this.actions$.subscribe(action => {
          const { type, ...rest } = action;
          return console.log(`${type} - ${JSON.stringify(rest)}`);
        });
      }
      rogerthat.callbacks.ready(() => {
        this.ngZone.run(() => {
          this.translate.use(getLanguage(rogerthat.user.language));
          if (hasCordova) {
            if (rogerthat.system.os === 'ios') {
              this.statusBar.styleDefault();
            } else {
              this.statusBar.backgroundColorByHexString(rogerthat.system.colors.primaryDark);
            }
          }
          this.rogerthatService.initialize();
        });
      });
    });
  }

  private shouldExitApp(): boolean {
    const whitelist = [
      '',
      '/',
    ];
    return whitelist.includes(this.router.url);
  }

  private exit() {
    rogerthat.app.exit();
  }

}
