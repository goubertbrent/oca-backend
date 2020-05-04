import { CommonModule } from '@angular/common';
import { HttpClientModule } from '@angular/common/http';
import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatButtonToggleModule } from '@angular/material/button-toggle';
import { MatRippleModule } from '@angular/material/core';
import { MatDialogModule } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTabsModule } from '@angular/material/tabs';
import { TranslateModule } from '@ngx-translate/core';
import { ImageCropperComponent } from './image-cropper/image-cropper.component';
import { UploadFileDialogComponent } from './upload-file-dialog/upload-file-dialog.component';

@NgModule({
  declarations: [ UploadFileDialogComponent, ImageCropperComponent ],
  imports: [
    CommonModule,
    FormsModule,
    HttpClientModule,
    TranslateModule,
    MatIconModule,
    MatTabsModule,
    MatButtonModule,
    MatDialogModule,
    MatProgressBarModule,
    MatRippleModule,
    MatButtonToggleModule,
  ],
  exports: [ UploadFileDialogComponent, ImageCropperComponent ],
})
export class UploadFileModule {
}
