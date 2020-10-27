import { HttpClient, HttpClientModule } from '@angular/common/http';
import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { RouteReuseStrategy, RouterModule, Routes } from '@angular/router';
import { StatusBar } from '@ionic-native/status-bar/ngx';
import { IonicModule, IonicRouteStrategy } from '@ionic/angular';
import { EffectsModule } from '@ngrx/effects';
import { StoreModule } from '@ngrx/store';
import { MissingTranslationHandler, TranslateLoader, TranslateModule } from '@ngx-translate/core';
import { RogerthatEffects } from '@oca/rogerthat';
import { CUSTOM_LOCALE_PROVIDER, HttpLoaderFactory, MissingTranslationWarnHandler } from '@oca/shared';
import { environment } from '../environments/environment';
import { AppComponent } from './app.component';
import { metaReducers, state } from './state';

const routes: Routes = [
  { path: 'signin', loadChildren: () => import('./register/signin.module').then(m => m.SigninModule) },
  { path: 'feed', loadChildren: () => import ('./feed/feed.module').then(m => m.FeedModule) },
];

@NgModule({
  declarations: [AppComponent],
  imports: [
    BrowserModule,
    // Required for @angular/material
    BrowserAnimationsModule,
    IonicModule.forRoot(),
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
    RouterModule.forRoot(routes),
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
    environment.extraAppImports,
  ],
  providers: [
    StatusBar,
    CUSTOM_LOCALE_PROVIDER,
    { provide: RouteReuseStrategy, useClass: IonicRouteStrategy },
  ],
  bootstrap: [AppComponent],
})
export class AppModule {
}
