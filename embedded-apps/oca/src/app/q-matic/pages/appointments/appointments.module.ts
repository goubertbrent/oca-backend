import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { IonicModule } from '@ionic/angular';
import { TranslateModule } from '@ngx-translate/core';
import { BackButtonModule } from '../../../shared/back-button/back-button.module';
import { AppointmentCardModule } from '../../appointment-card/appointment-card.module';
import { AppointmentsPage } from './appointments.page';

@NgModule({
  imports: [
    IonicModule,
    CommonModule,
    FormsModule,
    RouterModule.forChild([{ path: '', component: AppointmentsPage }]),
    TranslateModule,
    BackButtonModule,
    AppointmentCardModule,
  ],
  declarations: [AppointmentsPage],
})
export class AppointmentsModule {
}
