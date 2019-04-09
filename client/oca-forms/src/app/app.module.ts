import { registerLocaleData } from '@angular/common';
import localeFr from '@angular/common/locales/fr';
import localeNl from '@angular/common/locales/nl';
import { LOCALE_ID, NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { RouterModule } from '@angular/router';
import { EffectsModule } from '@ngrx/effects';
import { StoreModule } from '@ngrx/store';
import { StoreDevtoolsModule } from '@ngrx/store-devtools';
import { environment } from '../environments/environment';
import { AppComponent } from './app.component';
import { metaReducers, reducers } from './reducers';
import { routes } from './routes';
import { SharedModule } from './shared/shared.module';


registerLocaleData(localeNl);
registerLocaleData(localeFr);

const DEFAULT_LOCALE = 'en-US';
const SUPPORTED_LOCALES = [ 'en', 'nl', 'fr' ];
const locale = SUPPORTED_LOCALES.some(loc => navigator.language.startsWith(loc)) ? navigator.language : DEFAULT_LOCALE;

@NgModule({
  declarations: [
    AppComponent,
  ],
  imports: [
    BrowserModule,
    BrowserAnimationsModule,
    RouterModule.forRoot(routes),
    StoreModule.forRoot(reducers, { metaReducers }),
    StoreDevtoolsModule.instrument({ maxAge: 25, logOnly: environment.production }),
    EffectsModule.forRoot([]),
    SharedModule,
  ],
  providers: [ {
    provide: LOCALE_ID,
    useValue: locale,
  } ],
  bootstrap: [ AppComponent ],
  exports: [ SharedModule ],
})
export class AppModule {
}
