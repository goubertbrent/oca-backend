import { STEPPER_GLOBAL_OPTIONS } from '@angular/cdk/stepper';
import { HttpClient, HttpClientModule } from '@angular/common/http';
import { Injectable, NgModule } from '@angular/core';
import { ReactiveFormsModule } from '@angular/forms';
import { MatNativeDateModule } from '@angular/material/core';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatStepperModule } from '@angular/material/stepper';
import { BrowserModule } from '@angular/platform-browser';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
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
import { CUSTOM_LOCALE_PROVIDER, HttpLoaderFactory, MissingTranslationWarnHandler } from '@oca/shared';
import { IonicSelectableModule } from 'ionic-selectable';
import { Observable } from 'rxjs';
import { environment } from '../environments/environment';
import { CreateAppointmentComponent } from './components/create-appointment/create-appointment.component';
import { CreateAppointmentPageComponent } from './pages/create-appointment-page/create-appointment-page.component';

import { TimeblockrAppComponent } from './timeblockr-app.component';
import { timeblockrAppReducers } from './timeblockr.reducer';

@Injectable()
class CanActivateRoute implements CanActivate {

  constructor(private platform: Platform) {
  }

  canActivate(route: ActivatedRouteSnapshot, state: RouterStateSnapshot): Observable<boolean | UrlTree> |
    Promise<boolean | UrlTree> | boolean | UrlTree {
    return this.platform.ready().then(() => true);
  }

}

const routes: Routes = [
  { path: '', redirectTo: 'appointments/create', pathMatch: 'full' },
  {
    canActivate: [CanActivateRoute],
    path: 'appointments/create',
    component: CreateAppointmentPageComponent,
  }];

@NgModule({
  declarations: [
    TimeblockrAppComponent,
    CreateAppointmentComponent,
    CreateAppointmentPageComponent,
  ],
  imports: [
    BrowserModule,
    BrowserAnimationsModule,
    RouterModule.forRoot(routes),
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
    StoreModule.forRoot(timeblockrAppReducers, {
      runtimeChecks: {
        strictStateImmutability: true,
        strictActionImmutability: true,
        strictStateSerializability: true,
        strictActionSerializability: true,
        strictActionTypeUniqueness: true,
        strictActionWithinNgZone: true,
      },
    }),
    // StoreDevtoolsModule.instrument({
    //   maxAge: 25,
    //   name: 'OSA Timeblockr',
    //   logOnly: environment.production,
    // }),
    EffectsModule.forRoot([RogerthatEffects, ...environment.ngrxEffects]),
    ReactiveFormsModule,
    IonicSelectableModule,
    MatFormFieldModule,
    MatDatepickerModule,
    MatNativeDateModule,
    MatInputModule,
    MatStepperModule,
  ],
  providers: [
    CanActivateRoute,
    StatusBar,
    CUSTOM_LOCALE_PROVIDER,
    { provide: RouteReuseStrategy, useClass: IonicRouteStrategy },
    { provide: STEPPER_GLOBAL_OPTIONS, useValue: { displayDefaultIndicatorType: false } },
  ],
  bootstrap: [TimeblockrAppComponent],
})
export class TimeblockrModule {
}
