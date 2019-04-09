import { AgmCoreModule } from '@agm/core';
import { CommonModule } from '@angular/common';
import { HttpClient, HttpClientModule } from '@angular/common/http';
import { NgModule } from '@angular/core';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import {
  MAT_FORM_FIELD_DEFAULT_OPTIONS,
  MatAutocompleteModule,
  MatButtonModule,
  MatCardModule,
  MatDialogModule,
  MatIconModule,
  MatInputModule,
  MatListModule,
  MatProgressBarModule,
  MatProgressSpinnerModule,
  MatTabsModule,
} from '@angular/material';
import { EffectsModule } from '@ngrx/effects';
import { StoreModule } from '@ngrx/store';
import { MissingTranslationHandler, TranslateLoader, TranslateModule, TranslateService } from '@ngx-translate/core';
import { TranslateHttpLoader } from '@ngx-translate/http-loader';
import { GoogleChartsModule } from 'angular-google-charts';
import { SIMPLEMDE_CONFIG, SimplemdeModule } from 'ng2-simplemde';
import { Options as SimpleMDEOptions } from 'simplemde';
import { environment } from '../../environments/environment';
import { SimpleDialogComponent } from './dialog/simple-dialog.component';
import { ImageCropperComponent } from './image-cropper/image-cropper.component';
import { LoadableComponent } from './loadable/loadable.component';
import { SharedEffects } from './shared.effects';
import { sharedReducer } from './shared.reducer';
import { UploadImageDialogComponent } from './upload-image-dialog/upload-image-dialog.component';
import { UserAutoCompleteDialogComponent } from './users/components/user-auto-complete-dialog/user-auto-complete-dialog.component';
import { UserAutocompleteComponent } from './users/components/user-autocomplete/user-autocomplete.component';
import { MissingTranslationWarnHandler } from './util/missing-translation-handler';

// AoT requires an exported function for factories
export function HttpLoaderFactory(http: HttpClient) {
  return new TranslateHttpLoader(http, '/common/i18n/', '.json');
}

@NgModule({
  declarations: [
    ImageCropperComponent,
    SimpleDialogComponent,
    LoadableComponent,
    UserAutocompleteComponent,
    UserAutoCompleteDialogComponent,
    UploadImageDialogComponent,
  ],
  imports: [
    GoogleChartsModule.forRoot(),
    AgmCoreModule.forRoot({
      apiKey: environment.googleMapsKey,
    }),
    SimplemdeModule.forRoot({
      provide: SIMPLEMDE_CONFIG,
      useValue: {
        autoDownloadFontAwesome: false,
        spellChecker: false,
        status: false,
        toolbar: [ 'bold', 'italic', 'strikethrough', 'unordered-list', 'link' ],
      } as SimpleMDEOptions,
    }),
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
    StoreModule.forFeature('shared', sharedReducer),
    EffectsModule.forFeature([ SharedEffects ]),
    HttpClientModule,
    FormsModule,
    ReactiveFormsModule,
    CommonModule,
    MatAutocompleteModule,
    MatButtonModule,
    MatCardModule,
    MatDialogModule,
    MatIconModule,
    MatInputModule,
    MatListModule,
    MatProgressBarModule,
    MatProgressSpinnerModule,
    MatTabsModule,
  ],
  entryComponents:
    [
      SimpleDialogComponent,
      UserAutoCompleteDialogComponent,
      UploadImageDialogComponent,
    ],
  providers: [ {
    provide: MAT_FORM_FIELD_DEFAULT_OPTIONS,
    useValue: {
      appearance: 'standard',
    },
  } ],
  exports: [
    GoogleChartsModule,
    AgmCoreModule,
    SimplemdeModule,
    TranslateModule,
    HttpClientModule,
    FormsModule,
    ReactiveFormsModule,
    CommonModule,
    MatAutocompleteModule,
    MatButtonModule,
    MatCardModule,
    MatDialogModule,
    MatIconModule,
    MatInputModule,
    MatListModule,
    MatProgressBarModule,
    MatProgressSpinnerModule,
    MatTabsModule,
    ImageCropperComponent,
    SimpleDialogComponent,
    LoadableComponent,
    UserAutocompleteComponent,
    UserAutoCompleteDialogComponent,
  ],
})
export class SharedModule {

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
