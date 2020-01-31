import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { SelectAllOptionComponent } from './select-all-option/select-all-option.component';


@NgModule({
  declarations: [SelectAllOptionComponent],
  imports: [
    CommonModule,
    MatCheckboxModule,
  ],
  exports: [SelectAllOptionComponent],
})
export class SelectAllOptionModule {
}
