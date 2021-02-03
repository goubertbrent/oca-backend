import { DragDropModule } from '@angular/cdk/drag-drop';
import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatChipsModule } from '@angular/material/chips';
import { MatNativeDateModule } from '@angular/material/core';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatExpansionModule } from '@angular/material/expansion';
import { MAT_FORM_FIELD_DEFAULT_OPTIONS, MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatListModule } from '@angular/material/list';
import { MatMenuModule } from '@angular/material/menu';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSelectModule } from '@angular/material/select';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { RouterModule, Routes } from '@angular/router';
import { EffectsModule } from '@ngrx/effects';
import { StoreModule } from '@ngrx/store';
import { TranslateModule } from '@ngx-translate/core';
import { MarkdownModule } from '@oca/web-shared';
import { ERROR_HANDLING_TRANLATIONS_PROVIDER } from '../../environments/config';
import { MediaListEditorModule } from '../shared/media-list-editor/media-list-editor.module';
import { MediaSelectorModule } from '../shared/media-selector/media-selector.module';
import { OpeningHoursModule } from '../shared/opening-hours/opening-hours.module';
import { SelectAutocompleteModule } from '../shared/select-autocomplete/select-autocomplete.module';
import { SharedModule } from '../shared/shared.module';
import { TimeInputModule } from '../shared/time-input/time-input.module';
import { UploadFileModule } from '../shared/upload-file';
import { OpeningHoursSettingsPageComponent } from './opening-hours/opening-hours-settings-page/opening-hours-settings-page.component';
import { PrivacySettingsPageComponent } from './privacy-settings/privacy-settings-page/privacy-settings-page.component';
import { ServiceAddressesEditorComponent } from './service-info/service-addresses-editor/service-addresses-editor.component';
import { ServiceInfoPageComponent } from './service-info/service-info-page/service-info-page.component';
import { ServiceSyncedValueEditorComponent } from './service-info/service-synced-value-editor/service-synced-value-editor.component';
import { SyncedValuesPreviewComponent } from './service-info/synced-values-preview/synced-values-preview.component';
import { SettingsEffects } from './settings.effects';
import { settingsReducer } from './settings.reducer';


const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'service-info' },
  { path: 'opening-hours', component: OpeningHoursSettingsPageComponent },
  { path: 'service-info', component: ServiceInfoPageComponent },
  { path: 'privacy', component: PrivacySettingsPageComponent },
];

@NgModule({
  declarations: [
    OpeningHoursSettingsPageComponent,
    ServiceInfoPageComponent,
    ServiceSyncedValueEditorComponent,
    ServiceAddressesEditorComponent,
    SyncedValuesPreviewComponent,
    PrivacySettingsPageComponent,
  ],
  imports: [
    CommonModule,
    RouterModule.forChild(routes),
    StoreModule.forFeature('settings', settingsReducer),
    EffectsModule.forFeature([SettingsEffects]),
    TranslateModule,
    MatFormFieldModule,
    MatProgressBarModule,
    FormsModule,
    MatSelectModule,
    MatDatepickerModule,
    MatNativeDateModule,
    MatInputModule,
    MatButtonModule,
    MatExpansionModule,
    MatIconModule,
    MatToolbarModule,
    MatTooltipModule,
    MediaSelectorModule,
    UploadFileModule,
    DragDropModule,
    MatListModule,
    MatChipsModule,
    SharedModule,
    MatSlideToggleModule,
    SelectAutocompleteModule,
    TimeInputModule,
    MarkdownModule,
    MatMenuModule,
    OpeningHoursModule,
    MediaListEditorModule,
  ],
  providers: [
    { provide: MAT_FORM_FIELD_DEFAULT_OPTIONS, useValue: { appearance: 'outline' } },
    ERROR_HANDLING_TRANLATIONS_PROVIDER,
  ],
})
export class SettingsModule {
}
