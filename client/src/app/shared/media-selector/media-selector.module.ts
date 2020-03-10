import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { TranslateModule } from '@ngx-translate/core';
import { MediaSelectorComponent } from './media-selector/media-selector.component';


@NgModule({
  declarations: [MediaSelectorComponent],
  imports: [
    CommonModule,
    MatButtonModule,
    MatIconModule,
    TranslateModule,
    MatInputModule,
    FormsModule,
    MatSelectModule,
  ],
  exports: [
    MediaSelectorComponent,
  ],
})
export class MediaSelectorModule {
}
