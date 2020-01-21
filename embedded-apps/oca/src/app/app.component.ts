import { ChangeDetectionStrategy, ChangeDetectorRef, Component, ViewEncapsulation } from '@angular/core';
import { Router } from '@angular/router';
import { SplashScreen } from '@ionic-native/splash-screen/ngx';
import { StatusBar } from '@ionic-native/status-bar/ngx';
import { Platform } from '@ionic/angular';
import { Actions } from '@ngrx/effects';
import { TranslateService } from '@ngx-translate/core';
import { RogerthatContext } from 'rogerthat-plugin';
import { RogerthatService } from './rogerthat/rogerthat.service';
import { setColor } from './shared/color-utils';
import { DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES } from './shared/consts';


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
              private router: Router) {
    this.initializeApp();
  }

  initializeApp() {
    this.translate.setDefaultLang(DEFAULT_LANGUAGE);
    this.platform.ready().then(() => {
      this.splashScreen.hide();
      this.platform.backButton.subscribe(() => {
        if (this.shouldExitApp()) {
          (navigator as any).app.exitApp();
        }
      });
      rogerthat.callbacks.ready(() => {
        this.useLanguage(rogerthat.user.language);
        if (rogerthat.system.hasOwnProperty('colors')) {
          // @ts-ignore
          setColor('primary', rogerthat.system.colors.primary);
          if (rogerthat.system.os === 'ios') {
            this.statusBar.styleDefault();
          } else {
            // @ts-ignore
            this.statusBar.backgroundColorByHexString(rogerthat.system.colors.primaryDark);
          }
        } else {
          this.statusBar.styleDefault();
        }
        this.rogerthatService.initialize();
        this.rogerthatService.getContext().subscribe(context => {
          this.router.navigate(this.getRootPage(context));
        });
      });
    });
    this.actions$.subscribe(action => {
      const { type, ...rest } = action;
      return console.log(`${type} - ${JSON.stringify(rest)}`);
    });
  }

  private shouldExitApp(): boolean {
    const whitelist = ['/q-matic/appointments', '/jcc-appointments/appointments'];
    return whitelist.includes(this.router.url);
  }

  private getRootPage(context: RogerthatContext | null): string[] {
    const TAGS = {
      Q_MATIC: sha256('__sln__.q_matic'),
      JCC_APPOINTMENTS: sha256('__sln__.jcc_appointments'),
    };
    switch (rogerthat.menuItem.hashedTag) {
      case TAGS.Q_MATIC:
        return ['q-matic'];
      case TAGS.JCC_APPOINTMENTS:
        return ['jcc-appointments'];
      default:
        return ['q-matic'];
    }
  }

  private useLanguage(language: string) {
    let lang;
    if (SUPPORTED_LANGUAGES.indexOf(language) === -1) {
      const split = language.split('_')[ 0 ];
      if (SUPPORTED_LANGUAGES.indexOf(split) === -1) {
        lang = DEFAULT_LANGUAGE;
      } else {
        lang = split;
      }
    } else {
      lang = language;
    }
    console.log(`Set language to ${lang}`);
    this.translate.use(lang);
  }

}
