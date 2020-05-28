import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { ReactiveFormsModule } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatTooltipModule } from '@angular/material/tooltip';
import { TranslateModule } from '@ngx-translate/core';
import { TimeInputComponent } from './time-input.component';


@NgModule({
  declarations: [TimeInputComponent],
  imports: [
    CommonModule,
    MatFormFieldModule,
    MatInputModule,
    TranslateModule,
    MatIconModule,
    MatTooltipModule,
    ReactiveFormsModule,
  ],
  exports: [
    TimeInputComponent,
  ],
})
export class TimeInputModule {
}
