import { HttpClient, HttpClientModule } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { EffectsModule } from '@ngrx/effects';
import { StoreModule } from '@ngrx/store';
import { TranslateLoader, TranslateModule } from '@ngx-translate/core';
import { AppRoutingModule } from '../app/app-routing.module';
import { HttpLoaderFactory } from '../app/app.module';
import { qmaticReducer } from '../app/q-matic/q-matic-reducer';
import { QMaticEffects } from '../app/q-matic/q-matic.effects';
import { Q_MATIC_FEATURE } from '../app/q-matic/q-matic.state';
import { reducers } from '../app/reducers';
import { RogerthatEffects } from '../app/rogerthat/rogerthat.effect';

// TODO: define 'rogerthat' here
export const TESTING_MODULES = [
  HttpClientModule,
  FormsModule,
  StoreModule.forRoot({ ...reducers, [ Q_MATIC_FEATURE ]: qmaticReducer } as any),
  EffectsModule.forRoot([RogerthatEffects, QMaticEffects]),
  TranslateModule.forRoot({
    loader: {
      provide: TranslateLoader,
      useFactory: HttpLoaderFactory,
      deps: [HttpClient],
    },
  }),
  AppRoutingModule,
];
