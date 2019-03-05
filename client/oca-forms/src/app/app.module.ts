import { DragDropModule } from '@angular/cdk/drag-drop';
import { HttpClient, HttpClientModule } from '@angular/common/http';
import { NgModule } from '@angular/core';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import {
  MAT_FORM_FIELD_DEFAULT_OPTIONS,
  MatAutocompleteModule,
  MatButtonModule,
  MatCardModule,
  MatCheckboxModule,
  MatDatepickerModule,
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
} from '@angular/material';
import { BrowserModule } from '@angular/platform-browser';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { RouterModule } from '@angular/router';
import { EffectsModule } from '@ngrx/effects';
import { StoreModule } from '@ngrx/store';
import { MissingTranslationHandler, TranslateLoader, TranslateModule, TranslateService } from '@ngx-translate/core';
import { TranslateHttpLoader } from '@ngx-translate/http-loader';
import { GoogleChartsModule } from 'angular-google-charts';
import { AppComponent } from './app.component';
import { CreateFormPageComponent } from './create-form-page/create-form-page.component';
import { SimpleDialogComponent } from './dialog/simple-dialog.component';
import { EditFormSectionComponent } from './edit-form-section/edit-form-section.component';
import { EditFormTombolaComponent } from './edit-form-tombola/edit-form-tombola.component';
import { EditFormComponent } from './edit-form/edit-form.component';
import { FormDetailComponent } from './form-detail/form-detail.component';
import { FormDetailsPageComponent } from './form-details-page/form-details-page.component';
import { FormFieldComponent } from './form-field/form-field.component';
import { FormListPageComponent } from './form-list-page/form-list-page.component';
import { FormListComponent } from './form-list/form-list.component';
import { FormStatisticsNumberChartComponent } from './form-statistics-number-chart/form-statistics-number-chart.component';
import { FormStatisticsComponent } from './form-statistics/form-statistics.component';
import { FormValidatorsComponent } from './form-validators/form-validators.component';
import { FormsEffects } from './forms/forms.effects';
import { formsReducer } from './forms/forms.reducer';
import { LoadableComponent } from './loadable/loadable.component';
import { metaReducers, reducers } from './reducers';
import { routes } from './routes';
import { SelectInputListComponent } from './select-input-list/select-input-list.component';
import { UserAutoCompleteDialogComponent } from './users/components/user-auto-complete-dialog/user-auto-complete-dialog.component';
import { UserAutocompleteComponent } from './users/components/user-autocomplete/user-autocomplete.component';
import { MissingTranslationWarnHandler } from './util/missing-translation-handler';


const MATERIAL_MODULES = [
  MatAutocompleteModule,
  MatButtonModule,
  MatCardModule,
  MatCheckboxModule,
  MatDatepickerModule,
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
];
const EXPORTED_COMPONENTS = [
  FormListComponent,
  FormDetailComponent,
];

// Set via iframe
declare var LANGUAGE: string | undefined;

// AoT requires an exported function for factories
export function HttpLoaderFactory(http: HttpClient) {
  return new TranslateHttpLoader(http, '/common/i18n/', '.json');
}

@NgModule({
  declarations: [
    AppComponent,
    EXPORTED_COMPONENTS,
    FormStatisticsComponent,
    FormStatisticsNumberChartComponent,
    EditFormComponent,
    EditFormSectionComponent,
    FormFieldComponent,
    SelectInputListComponent,
    FormValidatorsComponent,
    FormListPageComponent,
    FormDetailsPageComponent,
    CreateFormPageComponent,
    SimpleDialogComponent,
    EditFormTombolaComponent,
    UserAutocompleteComponent,
    UserAutoCompleteDialogComponent,
    LoadableComponent,
  ],
  imports: [
    BrowserModule,
    BrowserAnimationsModule,
    FormsModule,
    ReactiveFormsModule,
    RouterModule.forRoot(routes),
    MATERIAL_MODULES,
    DragDropModule,
    HttpClientModule,
    TranslateModule.forRoot({
      loader: {
        provide: TranslateLoader,
        useFactory: HttpLoaderFactory,
        deps: [ HttpClient ],
      },
      missingTranslationHandler: {
        provide: MissingTranslationHandler,
        useClass: MissingTranslationWarnHandler,
      },
    }),
    GoogleChartsModule.forRoot(),
    StoreModule.forRoot(reducers, { metaReducers }),
    StoreModule.forFeature('forms', formsReducer),
    EffectsModule.forRoot([ FormsEffects ]),
  ],
  providers: [
    {
      provide: MAT_FORM_FIELD_DEFAULT_OPTIONS,
      useValue: {
        appearance: 'standard',
      },
    } ],
  bootstrap: [ AppComponent ],
  exports: [ MATERIAL_MODULES, EXPORTED_COMPONENTS ],
  entryComponents: [ SimpleDialogComponent, UserAutoCompleteDialogComponent ],
})
export class AppModule {
  constructor(private translate: TranslateService) {
    window.onmessage = e => {
      if (e.data && e.data.type === 'oca.set_language') {
        translate.use(e.data.language);
      }
    };
    translate.use('nl');
    translate.setDefaultLang('en');
  }
}
