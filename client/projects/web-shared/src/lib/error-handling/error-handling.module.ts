import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { MatDialogModule } from '@angular/material/dialog';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { StoreModule } from '@ngrx/store';
import { TranslateModule } from '@ngx-translate/core';
import { SimpleDialogModule } from '../simple-dialog';
import { ERROR_HANDLING_TRANSLATIONS, ErrorServiceTranslations } from './providers';


const MAT_IMPORTS = [
  MatSnackBarModule,
  MatDialogModule,
];

const messages: ErrorServiceTranslations = {
  error: 'Error',
  knownErrorKey: 'oca.error',
  unknownError: 'Unknown error',
  retry: 'Retry',
  close: 'Close',
};

@NgModule({
  declarations: [],
  imports: [
    MAT_IMPORTS,
    TranslateModule,
    StoreModule,
    CommonModule,
    SimpleDialogModule,
  ],
  providers: [
    { provide: ERROR_HANDLING_TRANSLATIONS, useValue: messages },
  ],
  exports: [MAT_IMPORTS],
})
export class ErrorHandlingModule {
}
