import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatDialogModule } from '@angular/material/dialog';
import { MatInputModule } from '@angular/material/input';
import { SimpleDialogComponent } from './simple-dialog.component';


@NgModule({
  declarations: [SimpleDialogComponent],
  imports: [
    MatDialogModule,
    MatInputModule,
    MatButtonModule,
    FormsModule,
    CommonModule,
  ],
  exports: [
    MatDialogModule,
    MatInputModule,
    MatButtonModule,
    SimpleDialogComponent
  ],
})
export class SimpleDialogModule {
}
