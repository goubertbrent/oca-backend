import { HttpClient, HttpClientModule } from '@angular/common/http';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { IonicModule } from '@ionic/angular';
import { EffectsModule } from '@ngrx/effects';
import { StoreModule } from '@ngrx/store';
import { MissingTranslationHandler, TranslateLoader, TranslateModule } from '@ngx-translate/core';
import { RogerthatEffects } from '@oca/rogerthat';
import { BackButtonModule, HttpLoaderFactory, MissingTranslationWarnHandler } from '@oca/shared';
import { environment } from '../../environments/environment';
import { metaReducers, state } from '../state';

export const TEST_MODULE_IMPORTS = [
  IonicModule.forRoot(),
  BrowserAnimationsModule,
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
  environment.extraAppImports,
  BackButtonModule,
];
