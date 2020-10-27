import { ChangeDetectionStrategy, ChangeDetectorRef, Component, NgZone } from '@angular/core';
import { Router } from '@angular/router';
import { StatusBar } from '@ionic-native/status-bar/ngx';
import { Config, isPlatform, Platform } from '@ionic/angular';
import { Actions } from '@ngrx/effects';
import { Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { RogerthatService } from '@oca/rogerthat';
import { DEFAULT_LANGUAGE, getLanguage, setColor } from '@oca/shared';
import { RogerthatContext, RogerthatContextType } from 'rogerthat-plugin';

@Component({
  selector: 'pp-root',
  templateUrl: 'app.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AppComponent {
  loaded = false;

  constructor(private platform: Platform,
              private statusBar: StatusBar,
              private translate: TranslateService,
              private store: Store,
              private router: Router,
              private actions: Actions,
              private rogerthatService: RogerthatService,
              private changeDetectorRef: ChangeDetectorRef,
              private ngZone: NgZone,
              private config: Config) {
    this.initializeApp().catch(err => console.error(err));
  }

  async initializeApp() {
    this.translate.setDefaultLang(DEFAULT_LANGUAGE);
    await this.platform.ready();
    this.platform.backButton.subscribe(() => {
      if (this.shouldExitApp()) {
        (navigator as any).app.exitApp();
      }
    });
    rogerthat.callbacks.ready(() => {
      this.ngZone.run(() => {
        this.rogerthatService.initialize();
        // without this dirty trick rogerthat.user might not be set the moment we dispatch the actions to
        // fetch data using rogerthat.user.communityId
        this.loaded = true;
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
        this.rogerthatService.getContext().subscribe(context => this.processContext(context));
        if (isPlatform('ios')) {
          this.translate.get('back').subscribe(back => {
            this.config.set('backButtonText', back);
          });
        }
        this.changeDetectorRef.markForCheck();
      });
    });
    this.actions.subscribe(action => {
      if (rogerthat.system.debug) {
        console.log(JSON.stringify(action));
      }
    });
  }

  private shouldExitApp(): boolean {
    const whitelist = ['/psp/overview', '/psp/merchants', '/psp/info'];
    return whitelist.includes(this.router.url);
  }

  private processContext(context: RogerthatContext | null) {
    if (context?.type) {
      switch (context.type) {
        case RogerthatContextType.QR_SCANNED:
        case RogerthatContextType.URL:
          this.router.navigate(['psp', 'overview'], { queryParams: { qr: context.data.content } });
          break;
      }
    }
  }
}
