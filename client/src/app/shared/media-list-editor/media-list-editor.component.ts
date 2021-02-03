import { CdkDragDrop, moveItemInArray } from '@angular/cdk/drag-drop';
import { ChangeDetectionStrategy, ChangeDetectorRef, Component, forwardRef, Input, ViewChild } from '@angular/core';
import { ControlValueAccessor, NG_VALUE_ACCESSOR } from '@angular/forms';
import { MatDialog } from '@angular/material/dialog';
import { TranslateService } from '@ngx-translate/core';
import { MediaType, SimpleDialogComponent, SimpleDialogData, SimpleDialogResult } from '@oca/web-shared';
import { MediaItem } from '../media-selector/media';
import { MediaSelectorComponent } from '../media-selector/media-selector/media-selector.component';
import { UploadFileDialogConfig } from '../upload-file';

@Component({
  selector: 'oca-media-list-editor',
  templateUrl: './media-list-editor.component.html',
  styleUrls: ['./media-list-editor.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  providers: [{
    provide: NG_VALUE_ACCESSOR,
    useExisting: forwardRef(() => MediaListEditorComponent),
    multi: true,
  }],
})
export class MediaListEditorComponent implements ControlValueAccessor {
  @ViewChild('mediaSelector') mediaSelector: MediaSelectorComponent;
  @Input() placeholderUrl?: string;
  @Input() uploadFileDialogConfig: Partial<UploadFileDialogConfig>;
  mediaItems: MediaItem[];

  disabled = false;
  MediaType = MediaType;
  newMedia: MediaItem | null = null;
  allowedMediaTypes = [MediaType.IMAGE, MediaType.VIDEO_YOUTUBE];

  constructor(private changeDetectorRef: ChangeDetectorRef,
              private matDialog: MatDialog,
              private translate: TranslateService) {
  }

  addMediaItem(media: MediaItem | null) {
    if (media && media.content?.trim()) {
      this.mediaItems = [media, ...this.mediaItems];
      this.onChange(this.mediaItems);
      this.newMedia = null;
    }
  }

  removeMedia(mediaItem: MediaItem) {
    this.matDialog.open<SimpleDialogComponent, SimpleDialogData, SimpleDialogResult>(SimpleDialogComponent, {
      data: {
        ok: this.translate.instant('oca.ok'),
        cancel: this.translate.instant('oca.Cancel'),
        title: this.translate.instant('oca.confirmation'),
        message: this.translate.instant('oca.confirm_delete_media'),
      },
    }).afterClosed().subscribe(result => {
      if (result?.submitted) {
        this.mediaItems = this.mediaItems.filter(m => m !== mediaItem);
        this.onChange(this.mediaItems);
        this.changeDetectorRef.markForCheck();
      }
    });
  }

  itemDropped(event: CdkDragDrop<MediaItem, any>) {
    moveItemInArray(this.mediaItems, event.previousIndex, event.currentIndex);
    this.onChange(this.mediaItems);
  }

  registerOnChange(fn: any): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: any): void {
    this.onTouched = fn;
  }

  setDisabledState(isDisabled: boolean): void {
    this.disabled = isDisabled;
    this.changeDetectorRef.markForCheck();
  }

  writeValue(values?: MediaItem[]): void {
    if (values) {
      this.mediaItems = values;
      this.changeDetectorRef.markForCheck();
    }
  }

  private onChange = (_: any) => {
  };
  private onTouched = () => {
  };

  addYoutubeVideo() {
    this.newMedia = {
      type: MediaType.VIDEO_YOUTUBE,
      content: '',
      thumbnail_url: null,
      file_reference: null,
    };
  }
}
