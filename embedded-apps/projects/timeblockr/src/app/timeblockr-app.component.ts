import { Location } from '@angular/common';
import { ChangeDetectionStrategy, Component, NgZone, ViewEncapsulation } from '@angular/core';
import { StatusBar } from '@ionic-native/status-bar/ngx';
import { Config, Platform } from '@ionic/angular';
import { Actions } from '@ngrx/effects';
import { Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { RogerthatService } from '@oca/rogerthat';
import { DEFAULT_LANGUAGE, getLanguage, setColor } from '@oca/shared';

@Component({
  selector: 'timeblockr-app',
  templateUrl: './timeblockr-app.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
})
export class TimeblockrAppComponent {

  constructor(private platform: Platform,
              private statusBar: StatusBar,
              private rogerthatService: RogerthatService,
              private translate: TranslateService,
              private actions$: Actions,
              private location: Location,
              private store: Store,
              private ngZone: NgZone,
              private config: Config) {
    this.initializeApp().catch(err => console.error(err));
  }

  async initializeApp() {
    this.translate.setDefaultLang(DEFAULT_LANGUAGE);
    this.platform.backButton.subscribe(async () => {
      if (this.shouldExitApp()) {
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
      });
      if (rogerthat.system.debug) {
        this.actions$.subscribe(action => {
          const { type, ...rest } = action;
          return console.log(`${type} - ${JSON.stringify(rest)}`);
        });
      }
    });
    if (this.platform.is('ios')) {
      this.translate.stream('app.timeblockr.back').subscribe(translation => {
        this.config.set('backButtonText', translation);
      });
    }
  }

  private shouldExitApp(): boolean {
    const whitelist = [
      '/appointments',
    ];
    return whitelist.includes(this.location.path());
  }

  private exit() {
    rogerthat.app.exit();
  }

}
