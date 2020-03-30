import { HTTP_INTERCEPTORS, HttpClient, HttpClientModule } from '@angular/common/http';
import { Injectable, NgModule } from '@angular/core';
import { MAT_FORM_FIELD_DEFAULT_OPTIONS } from '@angular/material/form-field';
import { BrowserModule } from '@angular/platform-browser';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { RouterModule, Routes } from '@angular/router';
import { EffectsModule } from '@ngrx/effects';
import { StoreModule } from '@ngrx/store';
import { StoreDevtoolsModule } from '@ngrx/store-devtools';
import { MissingTranslationHandler, MissingTranslationHandlerParams, TranslateLoader, TranslateModule } from '@ngx-translate/core';
import { TranslateHttpLoader } from '@ngx-translate/http-loader';
import { environment } from '../environments/environment';
import { AppComponent } from './app.component';
import { CUSTOM_LOCALE_PROVIDER } from './locales';
import { metaReducers, reducers } from './reducers';
import { MainHttpInterceptor } from './shared/main-http-interceptor';
import { SharedModule } from './shared/shared.module';

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
  { path: '', pathMatch: 'full', redirectTo: 'settings' },
  { path: 'forms', loadChildren: () => import('./forms/oca-forms.module').then(m => m.OcaFormsModule) },
  { path: 'participation', loadChildren: () => import('./participation/participation.module').then(m => m.ParticipationModule) },
  { path: 'news', loadChildren: () => import('./news/news.module').then(m => m.NewsModule) },
  { path: 'reports', loadChildren: () => import('./reports/reports.module').then(m => m.ReportsModule) },
  { path: 'admin', loadChildren: () => import('./admin/admin.module').then(m => m.AdminModule) },
  { path: 'settings', loadChildren: () => import('./settings/settings.module').then(m => m.SettingsModule) },
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
        deps: [HttpClient],
      },
      missingTranslationHandler: {
        provide: MissingTranslationHandler,
        useClass: MissingTranslationWarnHandler,
      },
    }),
    SharedModule,
  ],
  exports: [SharedModule],
  providers: [
    CUSTOM_LOCALE_PROVIDER,
    { provide: MAT_FORM_FIELD_DEFAULT_OPTIONS, useValue: { appearance: 'standard' }},
    { provide: HTTP_INTERCEPTORS, useClass: MainHttpInterceptor, multi: true },
  ],
  bootstrap: [AppComponent],
})
export class AppModule {
}
