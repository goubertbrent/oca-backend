import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatDialogModule } from '@angular/material/dialog';
import { MatInputModule } from '@angular/material/input';
import { RouterModule } from '@angular/router';
import { TranslateModule } from '@ngx-translate/core';
import { DIALOGS_COMPONENTS } from './components';

@NgModule({
  imports: [
    CommonModule,
    FormsModule,
    RouterModule,
    TranslateModule,
    MatButtonModule,
    MatInputModule,
    MatDialogModule,
  ],
  declarations: [
    DIALOGS_COMPONENTS,
  ],
  exports: [
    DIALOGS_COMPONENTS,
  ],
})
export class DialogModule {
}
