import { DragDropModule } from '@angular/cdk/drag-drop';
import { NgModule } from '@angular/core';
import {
  MatAutocompleteModule,
  MatButtonModule,
  MatCardModule,
  MatCheckboxModule,
  MatChipsModule,
  MatDatepickerModule,
  MatDialogModule,
  MatIconModule,
  MatInputModule,
  MatListModule,
  MatMenuModule,
  MatNativeDateModule,
  MatProgressBarModule,
  MatProgressSpinnerModule,
  MatRadioModule,
  MatSelectModule,
  MatSlideToggleModule,
  MatSnackBarModule,
  MatStepperModule,
  MatTabsModule,
  MatToolbarModule,
  MatTooltipModule,
} from '@angular/material';
import { RouterModule } from '@angular/router';
import { EffectsModule } from '@ngrx/effects';
import { StoreModule } from '@ngrx/store';
import { SharedModule } from '../shared/shared.module';
import { ArrangeSectionsDialogComponent } from './components/arange-sections-dialog/arrange-sections-dialog.component';
import { DateStatisticsListComponent } from './components/date-statistics-list/date-statistics-list.component';
import { EditFormSectionComponent } from './components/edit-form-section/edit-form-section.component';
import { EditFormComponent } from './components/edit-form/edit-form.component';
import { FormDetailComponent } from './components/form-detail/form-detail.component';
import { FormFieldComponent } from './components/form-field/form-field.component';
import { FormListComponent } from './components/form-list/form-list.component';
import { FormResponsesComponent } from './components/form-responses/form-responses.component';
import { FormStatisticsNumberChartComponent } from './components/form-statistics-number-chart/form-statistics-number-chart.component';
import { FormStatisticsComponent } from './components/form-statistics/form-statistics.component';
import { FormTombolaWinnersComponent } from './components/form-tombola-winners/form-tombola-winners.component';
import { FormValidatorsComponent } from './components/form-validators/form-validators.component';
import { SelectInputListComponent } from './components/select-input-list/select-input-list.component';
import { routes } from './forms-routes';
import { FormsEffects } from './forms.effects';
import { formsReducer } from './forms.reducer';
import { FormDetailsPageComponent } from './pages/form-details-page/form-details-page.component';
import { FormListPageComponent } from './pages/form-list-page/form-list-page.component';

@NgModule({
  declarations: [
    FormListComponent,
    FormDetailComponent,
    FormStatisticsComponent,
    FormStatisticsNumberChartComponent,
    EditFormComponent,
    EditFormSectionComponent,
    FormFieldComponent,
    SelectInputListComponent,
    FormValidatorsComponent,
    FormListPageComponent,
    FormDetailsPageComponent,
    FormTombolaWinnersComponent,
    ArrangeSectionsDialogComponent,
    DateStatisticsListComponent,
    FormResponsesComponent,
  ],
  imports: [
    SharedModule,
    StoreModule.forFeature('forms', formsReducer),
    EffectsModule.forFeature([ FormsEffects ]),
    RouterModule.forChild(routes),
    DragDropModule,
    MatAutocompleteModule,
    MatButtonModule,
    MatCardModule,
    MatCheckboxModule,
    MatChipsModule,
    MatDatepickerModule,
    MatDialogModule,
    MatIconModule,
    MatInputModule,
    MatListModule,
    MatMenuModule,
    MatNativeDateModule,
    MatProgressBarModule,
    MatProgressSpinnerModule,
    MatRadioModule,
    MatSelectModule,
    MatSlideToggleModule,
    MatSnackBarModule,
    MatStepperModule,
    MatTabsModule,
    MatToolbarModule,
    MatTooltipModule,
    MatProgressBarModule,
  ],
  entryComponents: [
    ArrangeSectionsDialogComponent,
  ],
})
export class OcaFormsModule {
}
