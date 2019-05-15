import { DragDropModule } from '@angular/cdk/drag-drop';
import { NgModule } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatChipsModule } from '@angular/material/chips';
import { MatNativeDateModule } from '@angular/material/core';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatDialogModule } from '@angular/material/dialog';
import { MAT_FORM_FIELD_DEFAULT_OPTIONS } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatListModule } from '@angular/material/list';
import { MatMenuModule } from '@angular/material/menu';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatRadioModule } from '@angular/material/radio';
import { MatSelectModule } from '@angular/material/select';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { MatStepperIntl, MatStepperModule } from '@angular/material/stepper';
import { MatTabsModule } from '@angular/material/tabs';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { RouterModule, Routes } from '@angular/router';
import { EffectsModule } from '@ngrx/effects';
import { StoreModule } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
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
import { ImageCropperComponent } from './components/image-cropper/image-cropper.component';
import { SelectInputListComponent } from './components/select-input-list/select-input-list.component';
import { UploadImageDialogComponent } from './components/upload-image-dialog/upload-image-dialog.component';
import { FormsEffects } from './forms.effects';
import { formsReducer } from './forms.reducer';
import { MatStepperIntlImpl } from './mat-stepper-intl-impl';
import { FormDetailsPageComponent } from './pages/form-details-page/form-details-page.component';
import { FormListPageComponent } from './pages/form-list-page/form-list-page.component';
import { EditNextActionDialogComponent } from './components/edit-next-action-dialog/edit-next-action-dialog.component';
import { NextActionEditorComponent } from './components/next-action-editor/next-action-editor.component';

const routes: Routes = [
  { path: '', component: FormListPageComponent },
  { path: ':id', component: FormDetailsPageComponent },
];

@NgModule({
  imports: [
    RouterModule.forChild(routes),
    StoreModule.forFeature('forms', formsReducer),
    EffectsModule.forFeature([ FormsEffects ]),
    SharedModule,
    DragDropModule,
    MatButtonModule,
    MatCardModule,
    MatCheckboxModule,
    MatChipsModule,
    MatDatepickerModule,
    MatDialogModule,
    MatDialogModule,
    MatIconModule,
    MatInputModule,
    MatListModule,
    MatMenuModule,
    MatNativeDateModule,
    MatProgressSpinnerModule,
    MatRadioModule,
    MatSelectModule,
    MatSlideToggleModule,
    MatSnackBarModule,
    MatTabsModule,
    MatToolbarModule,
    MatTooltipModule,
    MatProgressBarModule,
    MatStepperModule,
  ],
  exports: [],
  declarations: [
    FormResponsesComponent,
    UploadImageDialogComponent,
    ImageCropperComponent,
    DateStatisticsListComponent,
    ArrangeSectionsDialogComponent,
    FormTombolaWinnersComponent,
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
    EditNextActionDialogComponent,
    NextActionEditorComponent,
  ],
  entryComponents: [
    ArrangeSectionsDialogComponent,
    UploadImageDialogComponent,
    EditNextActionDialogComponent,
  ],
  providers: [
    { provide: MAT_FORM_FIELD_DEFAULT_OPTIONS, useValue: { appearance: 'standard' } },
    { provide: MatStepperIntl, useClass: MatStepperIntlImpl, deps: [ TranslateService ] },
  ],
})
export class OcaFormsModule {
}
