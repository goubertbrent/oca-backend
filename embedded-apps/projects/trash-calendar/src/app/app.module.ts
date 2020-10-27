import { CommonModule } from '@angular/common';
import { HttpClient, HttpClientModule } from '@angular/common/http';
import { Injectable, NgModule } from '@angular/core';
import { ReactiveFormsModule } from '@angular/forms';
import { BrowserModule } from '@angular/platform-browser';
import {
  ActivatedRouteSnapshot,
  CanActivate,
  RouteReuseStrategy,
  RouterModule,
  RouterStateSnapshot,
  Routes,
  UrlTree,
} from '@angular/router';
import { StatusBar } from '@ionic-native/status-bar/ngx';
import { IonicModule, IonicRouteStrategy, Platform } from '@ionic/angular';
import { EffectsModule } from '@ngrx/effects';
import { StoreModule } from '@ngrx/store';
import { MissingTranslationHandler, TranslateLoader, TranslateModule } from '@ngx-translate/core';
import { RogerthatEffects } from '@oca/rogerthat';
import { BackButtonModule, CUSTOM_LOCALE_PROVIDER, HttpLoaderFactory, MissingTranslationWarnHandler } from '@oca/shared';
import { IonicSelectableModule } from 'ionic-selectable';
import { Observable } from 'rxjs';
import { environment } from '../environments/environment';
import { AppComponent } from './app.component';
import { MainComponentComponent } from './pages/main-component/main-component.component';
import { NotificationsPageComponent } from './pages/notifications-page/notifications-page.component';
import { OverviewPageComponent } from './pages/overview-page/overview-page.component';
import { SetAddressPageComponent } from './pages/set-address-page/set-address-page.component';
import { metaReducers, state } from './state';


@Injectable()
class CanActivateRoute implements CanActivate {

  constructor(private platform: Platform) {
  }

  canActivate(route: ActivatedRouteSnapshot, routerStateSnapshot: RouterStateSnapshot): Observable<boolean | UrlTree> |
    Promise<boolean | UrlTree> | boolean | UrlTree {
    return this.platform.ready().then(() => true);
  }

}

const routes: Routes = [
  {
    canActivate: [CanActivateRoute],
    path: '',
    component: MainComponentComponent,
    children: [
      { path: '', redirectTo: 'overview', pathMatch: 'full' },
      { path: 'overview', component: OverviewPageComponent },
      { path: 'address', component: SetAddressPageComponent },
      { path: 'notifications', component: NotificationsPageComponent },
    ],
  },
];

@NgModule({
  declarations: [
    AppComponent,
    MainComponentComponent,
    OverviewPageComponent,
    SetAddressPageComponent,
    NotificationsPageComponent,
  ],
  imports: [
    BrowserModule,
    CommonModule,
    IonicModule.forRoot(environment.production ? {} : { mode: Math.random() > .5 ? 'ios' : 'md' }),
    HttpClientModule,
    TranslateModule.forRoot({
      loader: {
        provide: TranslateLoader,
        useFactory: HttpLoaderFactory,
        deps: [HttpClient],
      },
      missingTranslationHandler: {
        provide: MissingTranslationHandler,
        useClass: MissingTranslationWarnHandler,
      },
    }),
    EffectsModule.forRoot([RogerthatEffects, ...environment.ngrxEffects]),
    StoreModule.forRoot(state, {
      metaReducers: metaReducers as any,
      runtimeChecks: {
        strictStateImmutability: true,
        strictActionImmutability: true,
        strictActionWithinNgZone: true,
        strictStateSerializability: true,
        strictActionSerializability: true,
      },
    }),
    RouterModule.forRoot(routes),
    BackButtonModule,
    environment.extraImports,
    IonicSelectableModule,
    ReactiveFormsModule,
  ],
  providers: [
    CanActivateRoute,
    StatusBar,
    CUSTOM_LOCALE_PROVIDER,
    { provide: RouteReuseStrategy, useClass: IonicRouteStrategy },
  ],
  bootstrap: [AppComponent],
})
export class AppModule {
}
