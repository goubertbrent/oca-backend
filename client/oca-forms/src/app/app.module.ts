import { AgmCoreModule } from '@agm/core';
import { DragDropModule } from '@angular/cdk/drag-drop';
import { registerLocaleData } from '@angular/common';
import { HttpClient, HttpClientModule } from '@angular/common/http';
import localeFr from '@angular/common/locales/fr';
import localeNl from '@angular/common/locales/nl';
import { LOCALE_ID, NgModule } from '@angular/core';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import {
  MAT_FORM_FIELD_DEFAULT_OPTIONS,
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
import { environment } from '../environments/environment';
import { AppComponent } from './app.component';
import { SimpleDialogComponent } from './dialog/simple-dialog.component';
import { ArrangeSectionsDialogComponent } from './forms/components/arange-sections/arrange-sections-dialog.component';
import { EditFormSectionComponent } from './forms/components/edit-form-section/edit-form-section.component';
import { EditFormComponent } from './forms/components/edit-form/edit-form.component';
import { FormDetailComponent } from './forms/components/form-detail/form-detail.component';
import { FormFieldComponent } from './forms/components/form-field/form-field.component';
import { FormListComponent } from './forms/components/form-list/form-list.component';
import { FormStatisticsNumberChartComponent } from './forms/components/form-statistics-number-chart/form-statistics-number-chart.component';
import { FormStatisticsComponent } from './forms/components/form-statistics/form-statistics.component';
import { FormTombolaWinnersComponent } from './forms/components/form-tombola-winners/form-tombola-winners.component';
import { FormValidatorsComponent } from './forms/components/form-validators/form-validators.component';
import { FormsEffects } from './forms/forms.effects';
import { formsReducer } from './forms/forms.reducer';
import { CreateFormPageComponent } from './forms/pages/create-form-page/create-form-page.component';
import { FormDetailsPageComponent } from './forms/pages/form-details-page/form-details-page.component';
import { FormListPageComponent } from './forms/pages/form-list-page/form-list-page.component';
import { LoadableComponent } from './loadable/loadable.component';
import { metaReducers, reducers } from './reducers';
import { routes } from './routes';
import { SelectInputListComponent } from './select-input-list/select-input-list.component';
import { UserAutoCompleteDialogComponent } from './users/components/user-auto-complete-dialog/user-auto-complete-dialog.component';
import { UserAutocompleteComponent } from './users/components/user-autocomplete/user-autocomplete.component';
import { MissingTranslationWarnHandler } from './util/missing-translation-handler';
import { DateStatisticsListComponent } from './forms/components/date-statistics-list/date-statistics-list.component';

// AoT requires an exported function for factories
export function HttpLoaderFactory(http: HttpClient) {
  return new TranslateHttpLoader(http, '/common/i18n/', '.json');
}

registerLocaleData(localeNl);
registerLocaleData(localeFr);

const DEFAULT_LOCALE = 'en-US';
const SUPPORTED_LOCALES = [ 'en', 'nl', 'fr' ];
const locale = SUPPORTED_LOCALES.some(loc => navigator.language.startsWith(loc)) ? navigator.language : DEFAULT_LOCALE;

@NgModule({
  declarations: [
    AppComponent,
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
    CreateFormPageComponent,
    SimpleDialogComponent,
    FormTombolaWinnersComponent,
    UserAutocompleteComponent,
    UserAutoCompleteDialogComponent,
    LoadableComponent,
    ArrangeSectionsDialogComponent,
    DateStatisticsListComponent,
  ],
  imports: [
    BrowserModule,
    BrowserAnimationsModule,
    FormsModule,
    ReactiveFormsModule,
    RouterModule.forRoot(routes),
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
    AgmCoreModule.forRoot({
      apiKey: environment.googleMapsKey,
    }),
    StoreModule.forRoot(reducers, { metaReducers }),
    StoreModule.forFeature('forms', formsReducer),
    EffectsModule.forRoot([ FormsEffects ]),
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
    MatProgressSpinnerModule,
    MatRadioModule,
    MatSelectModule,
    MatSlideToggleModule,
    MatSnackBarModule,
    MatTabsModule,
    MatToolbarModule,
    MatTooltipModule,
  ],
  providers: [ {
    provide: MAT_FORM_FIELD_DEFAULT_OPTIONS,
    useValue: {
      appearance: 'standard',
    },
  }, {
    provide: LOCALE_ID,
    useValue: locale,
  } ],
  bootstrap: [ AppComponent ],
  entryComponents: [ SimpleDialogComponent, UserAutoCompleteDialogComponent, ArrangeSectionsDialogComponent ],
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
