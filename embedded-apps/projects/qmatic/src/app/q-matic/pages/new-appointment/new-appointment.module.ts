import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { ReactiveFormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { IonicModule } from '@ionic/angular';
import { TranslateModule } from '@ngx-translate/core';
import { IonicSelectableModule } from 'ionic-selectable';
import { CreateAppointmentComponent } from './create-appointment/create-appointment.component';
import { NewAppointmentPage } from './new-appointment.page';

@NgModule({
  imports: [
    IonicModule,
    CommonModule,
    ReactiveFormsModule,
    RouterModule.forChild([{ path: '', component: NewAppointmentPage }]),
    TranslateModule,
    IonicSelectableModule,
  ],
  declarations: [NewAppointmentPage, CreateAppointmentComponent],
})
export class NewAppointmentModule {
}
