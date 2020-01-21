import { CommonModule, DatePipe } from '@angular/common';
import { NgModule } from '@angular/core';
import { IonicModule } from '@ionic/angular';
import { TranslateModule } from '@ngx-translate/core';
import { AppointmentProductsOverviewComponentModule } from '../appointment-products-overview/appointment-products-overview.module';

import { AppointmentDetailsComponent } from './appointment-details.component';

@NgModule({
  imports: [CommonModule, TranslateModule, IonicModule, AppointmentProductsOverviewComponentModule],
  exports: [AppointmentDetailsComponent],
  declarations: [AppointmentDetailsComponent],
  providers: [DatePipe],
})
export class AppointmentDetailsModule {
}
