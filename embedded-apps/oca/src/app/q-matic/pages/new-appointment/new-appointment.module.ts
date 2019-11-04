import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { IonicModule } from '@ionic/angular';
import { TranslateModule } from '@ngx-translate/core';
import { AppointmentCardModule } from '../../appointment-card/appointment-card.module';
import { CreateAppointmentComponent } from './create-appointment/create-appointment.component';
import { NewAppointmentPage } from './new-appointment.page';

@NgModule({
  imports: [
    IonicModule,
    CommonModule,
    FormsModule,
    RouterModule.forChild([{ path: '', component: NewAppointmentPage }]),
    TranslateModule,
    AppointmentCardModule,
  ],
  declarations: [NewAppointmentPage, CreateAppointmentComponent],
})
export class NewAppointmentModule {
}
