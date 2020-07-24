import { AgmCoreModule } from '@agm/core';
import { CommonModule } from '@angular/common';
import { HttpClientModule } from '@angular/common/http';
import { NgModule } from '@angular/core';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MatAutocompleteModule } from '@angular/material/autocomplete';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatDialogModule } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatListModule } from '@angular/material/list';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { MatTabsModule } from '@angular/material/tabs';
import { CovalentTextEditorModule } from '@covalent/text-editor';
import { EffectsModule } from '@ngrx/effects';
import { StoreModule } from '@ngrx/store';
import { TranslateModule } from '@ngx-translate/core';
import { ErrorHandlingModule, SimpleDialogModule } from '@oca/web-shared';
import { GoogleChartsModule } from 'angular-google-charts';
import { ERROR_HANDLING_TRANLATIONS_PROVIDER } from '../../environments/config';
import { environment } from '../../environments/environment';
import { LoadableComponent } from './loadable/loadable.component';
import { SharedEffects } from './shared.effects';
import { sharedReducer } from './shared.reducer';
import { UserAutoCompleteDialogComponent } from './users/components/user-auto-complete-dialog/user-auto-complete-dialog.component';
import { UserAutocompleteComponent } from './users/components/user-autocomplete/user-autocomplete.component';
import { MaxValidator, MinValidator } from './validators/validators';

@NgModule({
  declarations: [
    LoadableComponent,
    UserAutocompleteComponent,
    UserAutoCompleteDialogComponent,
    MinValidator,
    MaxValidator,
  ],
  imports: [
    GoogleChartsModule.forRoot(),
    AgmCoreModule.forRoot({
      apiKey: environment.googleMapsKey,
      libraries: ['places'],
    }),
    CovalentTextEditorModule,
    TranslateModule,
    StoreModule.forFeature('shared', sharedReducer),
    EffectsModule.forFeature([SharedEffects]),
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
    MatSnackBarModule,
    MatTabsModule,
    SimpleDialogModule,
    ErrorHandlingModule,
  ],
  exports: [
    GoogleChartsModule,
    AgmCoreModule,
    CovalentTextEditorModule,
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
    MatSnackBarModule,
    MatTabsModule,
    LoadableComponent,
    UserAutocompleteComponent,
    UserAutoCompleteDialogComponent,
    MinValidator,
    MaxValidator,
    SimpleDialogModule,
    ErrorHandlingModule,
  ],
  providers: [ERROR_HANDLING_TRANLATIONS_PROVIDER],
})
export class SharedModule {
}
