import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { DynamicDatePipe } from './dynamic-date.pipe';


@NgModule({
  declarations: [DynamicDatePipe],
  exports: [
    DynamicDatePipe,
  ],
  imports: [
    CommonModule,
  ],
})
export class DynamicDateModule {
}
