import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MAT_FORM_FIELD_DEFAULT_OPTIONS, MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatListModule } from '@angular/material/list';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSelectModule } from '@angular/material/select';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatToolbarModule } from '@angular/material/toolbar';
import { RouterModule, Routes } from '@angular/router';
import { EffectsModule } from '@ngrx/effects';
import { StoreModule } from '@ngrx/store';
import { TranslateModule } from '@ngx-translate/core';
import { ERROR_HANDLING_TRANLATIONS_PROVIDER } from '../../environments/config';
import { MediaListEditorModule } from '../shared/media-list-editor/media-list-editor.module';
import { OpeningHoursModule } from '../shared/opening-hours/opening-hours.module';
import { SelectAutocompleteModule } from '../shared/select-autocomplete/select-autocomplete.module';
import { SharedModule } from '../shared/shared.module';
import { PointOfInterestFormComponent } from './components/point-of-interest-form/point-of-interest-form.component';
import { CreatePointOfInterestPageComponent } from './pages/create-point-of-interest-page/create-point-of-interest-page.component';
import { EditPointOfInterestPageComponent } from './pages/edit-point-of-interest-page/edit-point-of-interest-page.component';
import { PointOfInterestListPageComponent } from './pages/point-of-interest-list-page/point-of-interest-list-page.component';
import { PointOfInterestEffects } from './point-of-interest.effects';
import { pointOfInterestFeatureKey, pointOfInterestReducer } from './point-of-interest.reducer';

const routes: Routes = [
  { path: '', component: PointOfInterestListPageComponent },
  { path: 'detail/:id', component: EditPointOfInterestPageComponent },
  { path: 'create', component: CreatePointOfInterestPageComponent },
];

@NgModule({
  declarations: [
    PointOfInterestListPageComponent,
    EditPointOfInterestPageComponent,
    CreatePointOfInterestPageComponent,
    PointOfInterestFormComponent,
  ],
  imports: [
    CommonModule,
    RouterModule.forChild(routes),
    EffectsModule.forFeature([PointOfInterestEffects]),
    StoreModule.forFeature(pointOfInterestFeatureKey, pointOfInterestReducer),
    MatListModule,
    MatIconModule,
    MatButtonModule,
    MatToolbarModule,
    TranslateModule,
    MatProgressBarModule,
    MatFormFieldModule,
    MatInputModule,
    ReactiveFormsModule,
    MatSelectModule,
    SelectAutocompleteModule,
    OpeningHoursModule,
    MatSlideToggleModule,
    SharedModule,
    MediaListEditorModule,
  ],
  providers: [
    { provide: MAT_FORM_FIELD_DEFAULT_OPTIONS, useValue: { appearance: 'outline' } },
    ERROR_HANDLING_TRANLATIONS_PROVIDER,
  ],
})
export class PointOfInterestModule {
}
