import { registerLocaleData } from '@angular/common';
import { HttpClient, HttpClientModule } from '@angular/common/http';
import localeFr from '@angular/common/locales/fr';
import localeNl from '@angular/common/locales/nl';
import { LOCALE_ID, NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { Router, RouterModule, Routes } from '@angular/router';
import { EffectsModule } from '@ngrx/effects';
import { StoreModule } from '@ngrx/store';
import { StoreDevtoolsModule } from '@ngrx/store-devtools';
import { MissingTranslationHandler, TranslateLoader, TranslateModule, TranslateService } from '@ngx-translate/core';
import { TranslateHttpLoader } from '@ngx-translate/http-loader';
import { environment } from '../environments/environment';
import { AppComponent } from './app.component';
import { metaReducers, reducers } from './reducers';
import { MissingTranslationWarnHandler } from './shared/util/missing-translation-handler';

registerLocaleData(localeNl);
registerLocaleData(localeFr);

// AoT requires an exported function for factories
export function HttpLoaderFactory(http: HttpClient) {
  return new TranslateHttpLoader(http, '/common/i18n/', '.json');
}

const DEFAULT_LOCALE = 'en-US';
const SUPPORTED_LOCALES = [ 'en', 'nl', 'fr' ];
const locale = SUPPORTED_LOCALES.some(loc => navigator.language.startsWith(loc)) ? navigator.language : DEFAULT_LOCALE;

export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'forms' },
  { path: 'forms', loadChildren: './forms/oca-forms.module#OcaFormsModule' },
  { path: 'participation', loadChildren: './participation/participation.module#ParticipationModule' },
];

@NgModule({
  declarations: [ AppComponent ],
  imports: [
    BrowserModule,
    BrowserAnimationsModule,
    HttpClientModule,
    RouterModule.forRoot(routes, { useHash: environment.production }),
    StoreModule.forRoot(reducers, { metaReducers }),
    StoreDevtoolsModule.instrument({ maxAge: 25, logOnly: environment.production }),
    EffectsModule.forRoot([]),
    TranslateModule.forRoot({
      loader: {
        provide: TranslateLoader,
        useFactory: HttpLoaderFactory,
        deps: [ HttpClient ],
      },
      missingTranslationHandler: {
        provide: MissingTranslationHandler,
        useClass: MissingTranslationWarnHandler,
      },
    }),
  ],
  exports: [],
  providers: [ {
    provide: LOCALE_ID,
    useValue: locale,
  } ],
  bootstrap: [ AppComponent ],
})
export class AppModule {
  constructor(private translate: TranslateService, private router: Router) {
    window.onmessage = e => {
      if (e.data && e.data.type === 'oca.set_language') {
        translate.use(e.data.language);
      }
      if (e.data && e.data.type === 'oca.load_page') {
        router.navigate(e.data.paths);
      }
    };
    translate.use('nl');
    translate.setDefaultLang('en');
  }
}
