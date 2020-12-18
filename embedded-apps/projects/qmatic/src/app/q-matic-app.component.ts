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
  selector: 'qm-root',
  templateUrl: 'q-matic-app.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
})
export class QMaticAppComponent {
  loaded = false;

  constructor(private platform: Platform,
              private statusBar: StatusBar,
              private rogerthatService: RogerthatService,
              private translate: TranslateService,
              private actions$: Actions,
              private router: Router,
              private cdRef: ChangeDetectorRef,
              private location: Location,
              private ngZone: NgZone) {
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
        this.loaded = true;
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
        this.cdRef.markForCheck();
        if (rogerthat.system.debug) {
          this.actions$.subscribe(action => {
            const { type, ...rest } = action;
            return console.log(`${type} - ${JSON.stringify(rest)}`);
          });
        }
      });
    });
  }

  private shouldExitApp(): boolean {
    const whitelist = ['/appointments'];
    return whitelist.includes(this.location.path());
  }

  private exit() {
    rogerthat.app.exit();
  }
}
