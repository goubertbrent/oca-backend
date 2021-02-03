import { DragDropModule } from '@angular/cdk/drag-drop';
import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatMenuModule } from '@angular/material/menu';
import { TranslateModule } from '@ngx-translate/core';
import { MediaSelectorModule } from '../media-selector/media-selector.module';
import { MediaListEditorComponent } from './media-list-editor.component';


@NgModule({
  declarations: [MediaListEditorComponent],
  imports: [
    CommonModule,
    MatMenuModule,
    DragDropModule,
    MatIconModule,
    MatButtonModule,
    TranslateModule,
    MediaSelectorModule,
    FormsModule,
  ],
  exports: [MediaListEditorComponent],
})
export class MediaListEditorModule {
}
