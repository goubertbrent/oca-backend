import {HttpClient, HttpClientModule} from '@angular/common/http';
import {NgModule} from '@angular/core';
import {MatToolbarModule} from '@angular/material/toolbar';
import {BrowserModule} from '@angular/platform-browser';
import {BrowserAnimationsModule} from '@angular/platform-browser/animations';
import {RouterModule, Routes} from '@angular/router';
import {EffectsModule} from '@ngrx/effects';
import {StoreModule} from '@ngrx/store';
import {StoreDevtoolsModule} from '@ngrx/store-devtools';
import {TranslateLoader, TranslateModule, TranslateService} from '@ngx-translate/core';
import {TranslateHttpLoader} from '@ngx-translate/http-loader';
import {ErrorService} from '@oca/web-shared';
import {Observable, of} from 'rxjs';
import {environment} from '../../../../src/environments/environment';
import {ErrorHandlingModule} from '../../../web-shared/src/lib/error-handling';
import {ERROR_HANDLING_TRANLATIONS_PROVIDER} from '../environments/config';
import {AppComponent} from './app.component';
import {AppEffects} from './app.effects';
import {reducers} from './app.reducer';
import {getInitialState} from './initial-state';
import {WebNavbarComponent} from './web-navbar/web-navbar.component';
import {MapModule} from "./map/map.module";
import {MaterialModule} from "./material/material.module";

const oca = getInitialState();

export class WebTranslateHttpLoader extends TranslateHttpLoader {
  getTranslation(lang: string): Observable<object> {
    if (oca && lang in oca?.translations) {
      return of(oca.translations[lang]);
    }
    return super.getTranslation(lang);
  }
}

export function HttpLoaderFactory(http: HttpClient) {
  return new WebTranslateHttpLoader(http, '/common/i18n/web/', '.json');
}

const routes: Routes = [
  {
    path: 'web/:cityUrlName',
    children: [
      {
        path: 'news', loadChildren: () => import('./news/news.module').then(m => m.NewsModule),
      },
      {
        path: 'map', loadChildren: () => import('./map/map.module').then(m => m.MapModule),
      }
    ],
  },
];

@NgModule({
  declarations: [
    AppComponent,
    WebNavbarComponent,
  ],
  imports: [
    BrowserModule,
    BrowserAnimationsModule,
    HttpClientModule,
    MapModule,
    MaterialModule,
    RouterModule.forRoot(routes, {paramsInheritanceStrategy: 'always'}),
    TranslateModule.forRoot({
      defaultLanguage: 'en',
      loader: {
        provide: TranslateLoader,
        useFactory: HttpLoaderFactory,
        deps: [HttpClient],
      },
    }),
    StoreModule.forRoot(reducers, {
      initialState: oca?.initialState,
      runtimeChecks: {
        strictActionImmutability: true,
        strictActionSerializability: true,
        strictActionWithinNgZone: true,
        strictStateImmutability: true,
        strictStateSerializability: true,
      },
    }),
    StoreDevtoolsModule.instrument({
      name: 'Our City App',
      maxAge: 25,
      logOnly: environment.production,
    }),
    EffectsModule.forRoot([AppEffects]),
    ErrorHandlingModule,
    MatToolbarModule,
  ],
  providers: [
    ErrorService,
    ERROR_HANDLING_TRANLATIONS_PROVIDER,
  ],
  bootstrap: [AppComponent],
})
export class AppModule {
  constructor(private translate: TranslateService) {
    this.translate.use(typeof oca === 'undefined' ? 'nl' : oca.mainLanguage);
  }
}
