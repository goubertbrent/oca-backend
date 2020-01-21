import { CommonModule, DatePipe } from '@angular/common';
import { NgModule } from '@angular/core';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MatExpansionModule } from '@angular/material';
import { RouterModule } from '@angular/router';
import { IonicModule } from '@ionic/angular';
import { TranslateModule } from '@ngx-translate/core';
import { IonicSelectableModule } from 'ionic-selectable';
import { AppointmentDetailsModule } from '../../appointment-details/appointment-details.module';
import { JccCreateAppointmentComponent } from './create-appointment/jcc-create-appointment.component';
import { JccContactDetailsComponent } from './jcc-contact-details/jcc-contact-details.component';
import { JccLocationTimeComponent } from './jcc-location-time/jcc-location-time.component';
import { JccNewAppointmentPage } from './jcc-new-appointment-page.component';

@NgModule({
  imports: [
    IonicModule,
    CommonModule,
    FormsModule,
    RouterModule.forChild([{ path: '', component: JccNewAppointmentPage }]),
    TranslateModule,
    IonicSelectableModule,
    MatExpansionModule,
    AppointmentDetailsModule,
  ],
  declarations: [
    JccNewAppointmentPage,
    JccCreateAppointmentComponent,
    JccLocationTimeComponent,
    JccContactDetailsComponent,
  ],
  providers: [DatePipe],
})
export class JccNewAppointmentModule {
}
