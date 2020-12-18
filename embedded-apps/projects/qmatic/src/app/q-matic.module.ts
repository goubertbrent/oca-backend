import { CommonModule, DatePipe } from '@angular/common';
import { HttpClient, HttpClientModule } from '@angular/common/http';
import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { PreloadAllModules, RouteReuseStrategy, RouterModule } from '@angular/router';
import { StatusBar } from '@ionic-native/status-bar/ngx';
import { IonicModule, IonicRouteStrategy } from '@ionic/angular';
import { EffectsModule } from '@ngrx/effects';
import { StoreModule } from '@ngrx/store';
import { StoreDevtoolsModule } from '@ngrx/store-devtools';
import { MissingTranslationHandler, TranslateLoader, TranslateModule } from '@ngx-translate/core';
import { RogerthatEffects } from '@oca/rogerthat';
import { BackButtonModule, CUSTOM_LOCALE_PROVIDER, HttpLoaderFactory, MissingTranslationWarnHandler } from '@oca/shared';
import { IonicSelectableModule } from 'ionic-selectable';
import { environment } from '../environments/environment';
import { QMaticAppComponent } from './q-matic-app.component';
import { AppointmentCardComponent } from './q-matic/appointment-card/appointment-card.component';
import { AppointmentsPage } from './q-matic/pages/appointments/appointments.page';
import { Q_MATIC_ROUTES } from './q-matic/q-matic-routes';
import { metaReducers, reducers } from './reducers';


@NgModule({
  declarations: [
    QMaticAppComponent,
    AppointmentsPage,
    AppointmentCardComponent,
  ],
  imports: [
    BrowserModule,
    BrowserAnimationsModule, // Required for @angular/material
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
    EffectsModule.forRoot([RogerthatEffects, ...environment.effects]),
    StoreModule.forRoot(reducers as any, {
      metaReducers,
      runtimeChecks: {
        strictStateImmutability: true,
        strictActionImmutability: true,
        strictStateSerializability: true,
        strictActionSerializability: true,
      },
    }),
    StoreDevtoolsModule.instrument({
      name: 'Q-Matic embedded app',
      maxAge: 25, // Retains last 25 states
      logOnly: environment.production, // Restrict extension to log-only mode
    }),
    IonicSelectableModule,
    RouterModule.forRoot(Q_MATIC_ROUTES, { preloadingStrategy: PreloadAllModules }),
    CommonModule,
    BackButtonModule,
  ],
  providers: [
    DatePipe,
    StatusBar,
    CUSTOM_LOCALE_PROVIDER,
    { provide: RouteReuseStrategy, useClass: IonicRouteStrategy },
  ],
  bootstrap: [QMaticAppComponent],
})
export class QMaticModule {
}
