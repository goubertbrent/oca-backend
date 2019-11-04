import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { IonicModule } from '@ionic/angular';
import { EffectsModule } from '@ngrx/effects';
import { StoreModule } from '@ngrx/store';
import { TranslateModule } from '@ngx-translate/core';
import { qmaticReducer } from './q-matic-reducer';
import { Q_MATIC_ROUTES } from './q-matic-routes';
import { QMaticEffects } from './q-matic.effects';
import { Q_MATIC_FEATURE } from './q-matic.state';


@NgModule({
  imports: [
    IonicModule,
    CommonModule,
    FormsModule,
    RouterModule.forChild(Q_MATIC_ROUTES),
    EffectsModule.forFeature([QMaticEffects]),
    StoreModule.forFeature(Q_MATIC_FEATURE, qmaticReducer),
    TranslateModule,
  ],
  exports: [],
  declarations: [],
})
export class QMaticModule {
}
