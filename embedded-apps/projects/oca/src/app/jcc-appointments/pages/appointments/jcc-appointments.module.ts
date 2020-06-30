import { CommonModule, DatePipe } from '@angular/common';
import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { IonicModule } from '@ionic/angular';
import { TranslateModule } from '@ngx-translate/core';
import { BackButtonModule } from '@oca/shared';
import { AppointmentProductsOverviewComponentModule } from '../../appointment-products-overview/appointment-products-overview.module';
import { JccAppointmentsPage } from './jcc-appointments-page.component';

@NgModule({
  imports: [
    IonicModule,
    CommonModule,
    FormsModule,
    RouterModule.forChild([{ path: '', component: JccAppointmentsPage }]),
    TranslateModule,
    BackButtonModule,
    AppointmentProductsOverviewComponentModule,
  ],
  declarations: [JccAppointmentsPage],
  providers: [DatePipe],
})
export class JccAppointmentsModule {
}
