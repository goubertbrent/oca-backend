import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { IonicModule } from '@ionic/angular';
import { TranslateModule } from '@ngx-translate/core';
import { AppointmentCardComponent } from './appointment-card.component';

@NgModule({
  imports: [
    IonicModule,
    CommonModule,
    TranslateModule,
  ],
  declarations: [AppointmentCardComponent],
  exports: [AppointmentCardComponent],
})
export class AppointmentCardModule {
}
