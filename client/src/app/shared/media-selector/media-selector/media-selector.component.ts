import { ChangeDetectionStrategy, ChangeDetectorRef, Component, forwardRef, Input, OnChanges, SimpleChange } from '@angular/core';
import { ControlValueAccessor, NG_VALUE_ACCESSOR } from '@angular/forms';
import { MatDialog, MatDialogConfig } from '@angular/material/dialog';
import { TranslateService } from '@ngx-translate/core';
import { BaseMedia, MediaType } from '@oca/web-shared';
import { NEWS_MEDIA_TYPE_OPTIONS } from '../../../news/consts';
import { UploadedFileResult, UploadFileDialogComponent, UploadFileDialogConfig } from '../../upload-file';

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
  @Input() logoUrl?: string | null = null;
  @Input() allowedMediaTypes: (MediaType | null)[] = [null, MediaType.IMAGE, MediaType.YOUTUBE_VIDEO];

  media: BaseMedia | null = null;

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

  showImageDialog() {
    const config: MatDialogConfig<UploadFileDialogConfig> = {
      data: {
        uploadPrefix: 'news',
        title: this.translate.instant('oca.image'),
        gallery: { prefix: 'logo' },
      },
    };
    this.matDialog.open(UploadFileDialogComponent, config).afterClosed().subscribe((result?: UploadedFileResult) => {
      if (result) {
        this.setResult({ type: MediaType.IMAGE, content: result.getUrl() });
        this.changeDetectorRef.markForCheck();
      }
    });
  }

  useCoverPhoto() {
    if (this.logoUrl) {
      this.setResult({ type: MediaType.IMAGE, content: this.logoUrl });
    }
  }

  setYoutubeUrl(url: string | null) {
    if (url) {
      const id = this.getYoutubeVideoId(url);
      if (id) {
        this.setResult({ type: MediaType.YOUTUBE_VIDEO, content: id });
      }
    }
    this.youtubeUrl = url;
  }

  setResult(media: BaseMedia | null) {
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
      this.onChange(value);
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

  private onChange = (_: any) => {
  };
  private onTouched = () => {
  };
}
