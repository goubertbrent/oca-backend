import { Location } from '@angular/common';
import { ChangeDetectionStrategy, ChangeDetectorRef, Component, ViewEncapsulation } from '@angular/core';
import { Router } from '@angular/router';
import { SplashScreen } from '@ionic-native/splash-screen/ngx';
import { StatusBar } from '@ionic-native/status-bar/ngx';
import { Platform } from '@ionic/angular';
import { Actions, ofType } from '@ngrx/effects';
import { select, Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { RogerthatService } from '@oca/rogerthat';
import { DEFAULT_LOCALE, getLanguage, setColor } from '@oca/shared';
import { Observable } from 'rxjs';
import { GetUserInformationAction, GetUserInformationSuccessAction, HoplrActionTypes } from './hoplr.actions';
import { HoplrAppState, isUserInformationLoading } from './state';


@Component({
  selector: 'hoplr-root',
  templateUrl: 'app.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
})
export class AppComponent {
  loadingUserInfo$: Observable<boolean>;

  constructor(private platform: Platform,
              private splashScreen: SplashScreen,
              private statusBar: StatusBar,
              private rogerthatService: RogerthatService,
              private translate: TranslateService,
              private cdRef: ChangeDetectorRef,
              private actions$: Actions,
              private store: Store<HoplrAppState>,
              private location: Location,
              private router: Router) {
    this.initializeApp();
    this.loadingUserInfo$ = this.store.pipe(select(isUserInformationLoading));
  }

  async initializeApp() {
    this.translate.setDefaultLang(DEFAULT_LOCALE);
    await this.platform.ready();
    // @ts-ignore
    const hasCordova = typeof cordova !== 'undefined';
    if (hasCordova) {
      this.splashScreen.hide();
      this.platform.backButton.subscribe(async () => {
        if (await this.shouldExitApp()) {
          this.exit();
        }
      });
    }
    rogerthat.callbacks.ready(() => {
      this.translate.use(getLanguage(rogerthat.user.language));
      if (hasCordova) {
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
      }
      this.rogerthatService.initialize();

      this.store.dispatch(new GetUserInformationAction());
      if( ['', '/'].includes(this.location.path())) {
        this.actions$.pipe(ofType<GetUserInformationSuccessAction>(HoplrActionTypes.GET_USER_INFORMATION_SUCCESS)).subscribe(action =>{
          const page = action.payload.registered ? ['/feed'] : ['/signin'];
          this.router.navigate(page);
        });
      }
    });
    // this.actions$.subscribe(action => {
    //   const { type, ...rest } = action;
    //   return console.log(`${type} - ${JSON.stringify(rest)}`);
    // });
  }

  private async shouldExitApp(): Promise<boolean> {
    const whitelist = [
      '/signin',
      '/feed',
    ];
    return whitelist.includes(this.router.url);
  }

  private exit() {
    rogerthat.app.exit();
  }

}
