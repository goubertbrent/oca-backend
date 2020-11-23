import { Location } from '@angular/common';
import { ChangeDetectionStrategy, ChangeDetectorRef, Component, NgZone, ViewEncapsulation } from '@angular/core';
import { Router } from '@angular/router';
import { StatusBar } from '@ionic-native/status-bar/ngx';
import { Platform } from '@ionic/angular';
import { Actions, ofType } from '@ngrx/effects';
import { select, Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { RogerthatService } from '@oca/rogerthat';
import { DEFAULT_LANGUAGE, getLanguage } from '@oca/shared';
import { Observable } from 'rxjs';
import { take } from 'rxjs/operators';
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
              private statusBar: StatusBar,
              private rogerthatService: RogerthatService,
              private translate: TranslateService,
              private cdRef: ChangeDetectorRef,
              private ngZone: NgZone,
              private actions$: Actions,
              private store: Store<HoplrAppState>,
              private location: Location,
              private router: Router) {
    this.initializeApp();
    this.loadingUserInfo$ = this.store.pipe(select(isUserInformationLoading));
  }

  initializeApp() {
    // this.actions$.subscribe(action => {
    //   const { type, ...rest } = action;
    //   return console.log(`${type} - ${JSON.stringify(rest)}`);
    // });
    this.translate.setDefaultLang(DEFAULT_LANGUAGE);
    this.platform.ready().then(() => {
      // @ts-ignore
      const hasCordova = typeof cordova !== 'undefined';
      if (hasCordova) {
        this.platform.backButton.subscribe(() => {
          if (this.shouldExitApp()) {
            this.exit();
          }
        });
      }
      rogerthat.callbacks.ready(() => {
        this.ngZone.run(() => {
          this.store.dispatch(new GetUserInformationAction());
          this.translate.use(getLanguage(rogerthat.user.language));
          if (hasCordova) {
            if (rogerthat.system.os === 'ios') {
              this.statusBar.styleDefault();
            } else {
              this.statusBar.backgroundColorByHexString(rogerthat.system.colors.primaryDark);
            }
          }
          this.rogerthatService.initialize();

          if (['', '/'].includes(this.location.path())) {
            this.actions$.pipe(
              take(1),
              ofType<GetUserInformationSuccessAction>(HoplrActionTypes.GET_USER_INFORMATION_SUCCESS),
            ).subscribe(action => {
              const page = action.payload.registered ? ['/feed'] : ['/signin'];
              this.router.navigate(page).catch(err => {
                console.error(err);
              });
            });
          }
        });
      });
    });
  }

  private shouldExitApp(): boolean {
    const whitelist = [
      '',
      '/signin',
      '/feed',
    ];
    return whitelist.includes(this.location.path());
  }

  private exit() {
    rogerthat.app.exit();
  }

}
