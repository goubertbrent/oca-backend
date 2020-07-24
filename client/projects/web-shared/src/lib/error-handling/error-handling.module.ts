import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { MatDialogModule } from '@angular/material/dialog';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { StoreModule } from '@ngrx/store';
import { TranslateModule } from '@ngx-translate/core';
import { SimpleDialogModule } from '../simple-dialog';


const MAT_IMPORTS = [
  MatSnackBarModule,
  MatDialogModule,
];

@NgModule({
  declarations: [],
  imports: [
    MAT_IMPORTS,
    TranslateModule,
    StoreModule,
    CommonModule,
    SimpleDialogModule,
  ],
  exports: [MAT_IMPORTS],
})
export class ErrorHandlingModule {
}
