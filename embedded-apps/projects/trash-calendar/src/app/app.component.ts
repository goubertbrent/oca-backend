import { Location } from '@angular/common';
import { ChangeDetectionStrategy, ChangeDetectorRef, Component, NgZone, ViewEncapsulation } from '@angular/core';
import { Router } from '@angular/router';
import { StatusBar } from '@ionic-native/status-bar/ngx';
import { Platform } from '@ionic/angular';
import { Actions } from '@ngrx/effects';
import { TranslateService } from '@ngx-translate/core';
import { RogerthatService } from '@oca/rogerthat';
import { DEFAULT_LANGUAGE, getLanguage, setColor } from '@oca/shared';


@Component({
  selector: 'trash-root',
  templateUrl: 'app.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
})
export class AppComponent {

  constructor(private platform: Platform,
              private statusBar: StatusBar,
              private rogerthatService: RogerthatService,
              private translate: TranslateService,
              private cdRef: ChangeDetectorRef,
              private ngZone: NgZone,
              private actions$: Actions,
              private location: Location,
              private router: Router) {
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
