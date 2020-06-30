import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { IonicModule } from '@ionic/angular';
import { EffectsModule } from '@ngrx/effects';
import { StoreModule } from '@ngrx/store';
import { TranslateModule } from '@ngx-translate/core';
import { jccAppointmentsReducer } from './jcc-appointments-reducer';
import { JCC_APPOINTMENTS_ROUTES } from './jcc-appointments-routes';
import { JccAppointmentsEffects } from './jcc-appointments.effects';
import { JCC_APPOINTMENTS_FEATURE } from './jcc-appointments.state';


@NgModule({
  imports: [
    IonicModule,
    CommonModule,
    FormsModule,
    RouterModule.forChild(JCC_APPOINTMENTS_ROUTES),
    EffectsModule.forFeature([JccAppointmentsEffects]),
    StoreModule.forFeature(JCC_APPOINTMENTS_FEATURE, jccAppointmentsReducer),
    TranslateModule,
  ],
})
export class JccAppointmentsModule {
}
