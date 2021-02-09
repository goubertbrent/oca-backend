import { ChangeDetectionStrategy, ChangeDetectorRef, Component, forwardRef, Input, OnChanges, SimpleChange } from '@angular/core';
import { ControlValueAccessor, NG_VALUE_ACCESSOR } from '@angular/forms';
import { MatDialog, MatDialogConfig } from '@angular/material/dialog';
import { TranslateService } from '@ngx-translate/core';
import { MediaType } from '@oca/web-shared';
import { NEWS_MEDIA_TYPE_OPTIONS } from '../../../news/consts';
import { isUploadedFile, UploadedFileResult, UploadFileDialogComponent, UploadFileDialogConfig } from '../../upload-file';
import { MediaItem } from '../media';

@Component({
  selector: 'oca-media-selector',
  templateUrl: './media-selector.component.html',
  styleUrls: ['./media-selector.component.scss'],
  changeDetection: ChangeDetectionStrategy.Default,
  providers: [{
    provide: NG_VALUE_ACCESSOR,
    useExisting: forwardRef(() => MediaSelectorComponent),
    multi: true,
  }],
})
export class MediaSelectorComponent implements OnChanges, ControlValueAccessor {
  @Input() uploadFileDialogConfig: Partial<UploadFileDialogConfig>;
  @Input() logoUrl?: string | null = null;
  @Input() allowedMediaTypes: (MediaType | null)[] = [null, MediaType.IMAGE, MediaType.VIDEO_YOUTUBE];

  media: MediaItem | null = null;

  selectedMediaType: MediaType | null = MediaType.IMAGE;
  youtubeUrl: string | null;
  selectableMediaTypes: { label: string; value: MediaType | null }[] = NEWS_MEDIA_TYPE_OPTIONS;

  MediaType = MediaType;
  YOUTUBE_REGEX = new RegExp('^.*(youtu.be\\/|v\\/|embed\\/|watch\\?|youtube.com\\/user\\/[^#]*#([^\\/]*?\\/)*)\\??v?=?([^#\\&\\?]*).*');


  constructor(private translate: TranslateService,
              private matDialog: MatDialog,
              private changeDetectorRef: ChangeDetectorRef) {
  }

  ngOnChanges(changes: { [T in keyof this]: SimpleChange }): void {
    if (changes.allowedMediaTypes && this.allowedMediaTypes?.length) {
      this.selectedMediaType = this.media ? this.media.type : this.allowedMediaTypes[ 0 ];
    }
    if (changes.allowedMediaTypes && this.allowedMediaTypes) {
      this.selectableMediaTypes = NEWS_MEDIA_TYPE_OPTIONS.filter(t => this.allowedMediaTypes.includes(t.value));
    }
  }

  removeMedia() {
    this.setResult(null);
    this.setYoutubeUrl(null);
  }

  showFileSelectDialog(mediaType: MediaType) {
    const config: MatDialogConfig<UploadFileDialogConfig> = {
      data: {
        mediaType,
        uploadPrefix: '',
        title: this.translate.instant('oca.add_media'),
        accept: this.getContentType(mediaType),
        ...this.uploadFileDialogConfig,
      },
    };
    this.matDialog.open(UploadFileDialogComponent, config).afterClosed().subscribe((result?: UploadedFileResult) => {
      if (result) {
        if (isUploadedFile(result)) {
          this.setResult({
            type: result.type,
            content: result.url,
            thumbnail_url: result.thumbnail_url,
            file_reference: result.id,
          });
        } else {
          this.setResult({ type: result.type, content: result.url, thumbnail_url: result.thumbnail_url, file_reference: null });
        }
        this.changeDetectorRef.markForCheck();
      }
    });
  }

  useCoverPhoto() {
    if (this.logoUrl) {
      this.setResult({ type: MediaType.IMAGE, content: this.logoUrl, thumbnail_url: null, file_reference: null });
    }
  }

  setYoutubeUrl(url: string | null) {
    if (url) {
      const id = this.getYoutubeVideoId(url);
      if (id) {
        this.setResult({ type: MediaType.VIDEO_YOUTUBE, content: id, thumbnail_url: null, file_reference: null });
      }
    }
    this.youtubeUrl = url;
  }

  setResult(media: MediaItem | null) {
    this.media = media;
    this.onChange(this.media);
  }

  registerOnChange(fn: any): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: any): void {
    this.onTouched = fn;
  }

  setDisabledState(isDisabled: boolean) {
  }

  writeValue(value: any): void {
    if (value !== this.media) {
      this.media = value;
      if (this.media) {
        this.selectedMediaType = this.media.type;
      }
      this.changeDetectorRef.markForCheck();
    }
  }

  private getYoutubeVideoId(url: string) {
    const result = this.YOUTUBE_REGEX.exec(url);
    if (result) {
      return result[ 3 ];
    } else {
      return null;
    }
  }

  private getContentType(mediaType: MediaType) {
    switch (mediaType) {
      case MediaType.IMAGE:
      case MediaType.IMAGE_360:
        return 'image/*';
      case MediaType.VIDEO_YOUTUBE:
        return undefined;
      case MediaType.PDF:
        return 'application/pdf';
    }
  }

  private onChange = (_: any) => {
  };
  private onTouched = () => {
  };
}
