import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { MatInputModule } from '@angular/material/input';
import { TimePickerComponent } from './time-picker.component';


@NgModule({
  declarations: [TimePickerComponent],
  imports: [
    CommonModule,
    MatInputModule,
  ],
  exports: [
    TimePickerComponent,
  ],
})
export class TimePickerModule {
}
