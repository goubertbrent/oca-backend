import { CommonModule, DatePipe } from '@angular/common';
import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatTabsModule } from '@angular/material/tabs';
import { TranslateModule } from '@ngx-translate/core';
import { TimeInputModule } from '../time-input/time-input.module';
import { HoursPipe } from './hours.pipe';
import { OpeningHoursPeriodsEditorComponent } from './opening-hours-periods-editor/opening-hours-periods-editor.component';
import { OpeningHoursPeriodsComponent } from './opening-hours-periods/opening-hours-periods.component';
import { OpeningHoursComponent } from './opening-hours/opening-hours.component';


@NgModule({
  declarations: [
    OpeningHoursComponent,
    OpeningHoursPeriodsComponent,
    OpeningHoursPeriodsEditorComponent,
    HoursPipe,
  ],
  imports: [
    CommonModule,
    TranslateModule,
    MatFormFieldModule,
    MatSlideToggleModule,
    TimeInputModule,
    MatIconModule,
    MatDatepickerModule,
    MatTabsModule,
    FormsModule,
    MatButtonModule,
    MatExpansionModule,
    MatInputModule,
  ],
  providers: [HoursPipe, DatePipe],
  exports: [OpeningHoursComponent],
})
export class OpeningHoursModule {
}
