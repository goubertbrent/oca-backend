import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { TranslateModule } from '@ngx-translate/core';
import { TimeInputModule } from '../time-input/time-input.module';
import { DateTimeInputComponent } from './date-time-input.component';


@NgModule({
  declarations: [DateTimeInputComponent],
  imports: [
    CommonModule,
    FormsModule,
    MatFormFieldModule,
    MatInputModule,
    MatDatepickerModule,
    TranslateModule,
    TimeInputModule,
  ],
  exports: [
    DateTimeInputComponent,
  ],
})
export class DateTimeInputModule {
}
