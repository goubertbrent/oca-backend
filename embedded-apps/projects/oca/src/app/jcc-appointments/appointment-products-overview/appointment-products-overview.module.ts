import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { IonicModule } from '@ionic/angular';
import { TranslateModule } from '@ngx-translate/core';

import { AppointmentProductsOverviewComponent } from './appointment-products-overview.component';

@NgModule({
  imports: [
    IonicModule,
    TranslateModule,
    CommonModule,
  ],
  exports: [AppointmentProductsOverviewComponent],
  declarations: [AppointmentProductsOverviewComponent],
})
export class AppointmentProductsOverviewComponentModule {
}
