import { HttpClient, HttpClientModule } from '@angular/common/http';
import { Injectable, NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { ActivatedRoute, Router, RouterModule, Routes } from '@angular/router';
import { EffectsModule } from '@ngrx/effects';
import { StoreModule } from '@ngrx/store';
import { StoreDevtoolsModule } from '@ngrx/store-devtools';
import {
  MissingTranslationHandler,
  MissingTranslationHandlerParams,
  TranslateLoader,
  TranslateModule,
  TranslateService,
} from '@ngx-translate/core';
import { TranslateHttpLoader } from '@ngx-translate/http-loader';
import { environment } from '../environments/environment';
import { AppComponent } from './app.component';
import { CUSTOM_LOCALE_PROVIDER } from './locales';
import { metaReducers, reducers } from './reducers';

// AoT requires an exported function for factories
export function HttpLoaderFactory(http: HttpClient) {
  return new TranslateHttpLoader(http, '/common/i18n/', '.json');
}

@Injectable()
export class MissingTranslationWarnHandler implements MissingTranslationHandler {

  handle(params: MissingTranslationHandlerParams) {
    const lang = params.translateService.currentLang;
    console.warn(`Missing translation for key '${params.key}' for language '${lang}'`);
    return params.key;
  }
}

export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'forms' },
  { path: 'forms', loadChildren: () => import('./forms/oca-forms.module').then(m => m.OcaFormsModule) },
  { path: 'participation', loadChildren: () => import('./participation/participation.module').then(m => m.ParticipationModule) },
  { path: 'news', loadChildren: () => import('./news/news.module').then(m => m.NewsModule) },
];

@NgModule({
  declarations: [ AppComponent ],
  imports: [
    BrowserModule,
    BrowserAnimationsModule,
    HttpClientModule,
    RouterModule.forRoot(routes, { useHash: environment.production }),
    StoreModule.forRoot(reducers, {
      metaReducers, runtimeChecks: {
        // TODO: enable in dev mode
        strictActionImmutability: false,
        strictActionSerializability: false,
        strictStateImmutability: false,
        strictStateSerializability: false,
      },
    }),
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
  providers: [CUSTOM_LOCALE_PROVIDER],
  bootstrap: [ AppComponent ],
})
export class AppModule {
  constructor(private translate: TranslateService, private router: Router, private route: ActivatedRoute) {
    window.onmessage = e => {
      if (e.data && e.data.type === 'oca.set_language') {
        translate.use(e.data.language);
      }
      if (e.data && e.data.type === 'oca.load_page') {
        // When on a subpage of the desired page, don't do anything to keep state
        if (e.data.paths.length === 1) {
          if (route.snapshot.firstChild && route.snapshot.firstChild.routeConfig
            && route.snapshot.firstChild.routeConfig.path !== e.data.paths[ 0 ]) {
            router.navigate(e.data.paths);
          }
        }
      }
    };
    translate.use('nl');
    translate.setDefaultLang('en');
  }
}
