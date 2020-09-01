import { HttpClient, HttpErrorResponse, HttpEventType } from '@angular/common/http';
import { ChangeDetectionStrategy, ChangeDetectorRef, Component, Inject, OnDestroy, ViewChild } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { ProgressBarMode } from '@angular/material/progress-bar/progress-bar';
import { TranslateService } from '@ngx-translate/core';
import { Observable, Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { GcsFile, UploadedFile, UploadFileDialogConfig } from '../file-upload';
// noinspection ES6PreferShortImport
import { ImageCropperComponent } from '../image-cropper/image-cropper.component';
import { UploadFileService } from '../upload-file.service';


export class UploadedFileResult {
  constructor(public result: UploadedFile | GcsFile | string) {
  }

  getUrl(): string {
    return typeof this.result === 'string' ? this.result : this.result.url;
  }
}

@Component({
  selector: 'oca-upload-file-dialog',
  templateUrl: './upload-file-dialog.component.html',
  styleUrls: ['./upload-file-dialog.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class UploadFileDialogComponent implements OnDestroy {
  @ViewChild(ImageCropperComponent) imageCropper: ImageCropperComponent;

  selectedImageUrl: string | null = null;
  showProgress = false;
  uploadPercent = 0;
  progressMode: ProgressBarMode = 'indeterminate';
  uploadError: string | null = null;
  selectedFile: File | null = null;
  readonly images$: Observable<GcsFile[]>;
  readonly galleryImages$: Observable<GcsFile[]>;
  readonly showGallery: boolean;

  private destroyed$ = new Subject();
  private readonly supportedFileType: 'image' | undefined;

  constructor(@Inject(MAT_DIALOG_DATA) public data: UploadFileDialogConfig,
              private dialogRef: MatDialogRef<UploadFileDialogComponent>,
              private changeDetectorRef: ChangeDetectorRef,
              private uploadFileService: UploadFileService,
              private http: HttpClient,
              private translate: TranslateService) {
    this.showGallery = !!data.gallery;
    if (data.gallery) {
      this.galleryImages$ = this.uploadFileService.getGalleryFiles(data.gallery.prefix);
    }
    this.images$ = this.uploadFileService.getFiles(data.listPrefix);
    this.supportedFileType = data.fileType;
    data.accept = data.accept || 'image/*';
    data.cropOptions = {
      viewMode: 1,
      autoCropArea: 1,
      ...data.cropOptions,
    };
    data.croppedCanvasOptions = {
      maxWidth: 1440,
      fillColor: '#ffffff',
      imageSmoothingEnabled: true,
      imageSmoothingQuality: 'high' as any,
      ...data.croppedCanvasOptions,
    };
  }

  filePicked(file: GcsFile) {
    this.dialogRef.close(new UploadedFileResult(file));
  }

  removeFile() {
    this.selectedFile = null;
    this.selectedImageUrl = null;
    this.uploadError = null;
  }

  onFileSelected(event: Event) {
    this.progressMode = 'indeterminate';
    this.removeFile();
    const reader = new FileReader();
    const target = event.target as HTMLInputElement;
    if (target.files && target.files.length) {
      const file = target.files[ 0 ];
      this.selectedFile = file;
      if (this.supportedFileType === 'image' || this.data.croppedImageType || file.type.startsWith('image')) {
        this.showProgress = true;
        reader.readAsDataURL(file);
        reader.onload = () => {
          const dataUrl = reader.result as string;
          const contentType = dataUrl.substring(dataUrl.indexOf(':') + 1, dataUrl.indexOf(';'));
          if (!contentType.startsWith('image')) {
            this.showNotAnImageError();
            return;
          }
          this.selectedImageUrl = dataUrl;
          this.showProgress = false;
          this.changeDetectorRef.markForCheck();
        };
        reader.onerror = () => this.showNotAnImageError();
      }
    }
  }

  private showNotAnImageError() {
    this.selectedImageUrl = null;
    this.uploadError = this.translate.instant('oca.upload_file_image_error');
    this.showProgress = false;
    this.changeDetectorRef.markForCheck();
  }

  ngOnDestroy(): void {
    this.destroyed$.next();
    this.destroyed$.complete();
  }

  save() {
    if (this.uploadError) {
      return;
    }
    this.showProgress = true;
    this.progressMode = 'indeterminate';
    this.getFile().then(async blob => {
      this.progressMode = 'determinate';
      this.changeDetectorRef.markForCheck();
      if (!blob) {
        this.showProgress = false;
        return;
      }
      this.uploadFileService.uploadImage(blob, this.data.uploadPrefix, this.data.reference).pipe(
        takeUntil(this.destroyed$),
      ).subscribe(event => {
        switch (event.type) {
          case HttpEventType.UploadProgress:
            this.uploadPercent = (100 * event.loaded) / (event.total as number);
            break;
          case HttpEventType.Response:
            // Done - submit result
            this.showProgress = false;
            const body: UploadedFile = event.body as UploadedFile;
            this.dialogRef.close(new UploadedFileResult(body));
            break;
        }
        this.changeDetectorRef.markForCheck();
      }, e => this.handleUploadError(e));
    });
  }

  handleUploadError(error: any) {
    this.uploadPercent = 0;
    this.showProgress = false;
    if (error instanceof HttpErrorResponse && error.error && error.error.error) {
      this.uploadError = this.translate.instant(error.error.error, error.error.data);
    } else {
      this.uploadError = this.translate.instant('oca.upload_error_check_internet');
    }
    this.changeDetectorRef.markForCheck();
  }

  private getFile(): Promise<Blob | null> {
    if (!this.selectedFile) {
      return Promise.resolve(null);
    }
    if (this.data.croppedImageType || this.selectedFile.type.startsWith('image')) {
      // Always crop to jpeg unless it's a png (for transparent images so they don't lose the transparency)
      const croppedImageType = this.data.croppedImageType ?? (this.selectedFile.type === 'image/png' ? 'image/png' : 'image/jpeg');
      const options = this.data.croppedCanvasOptions;
      if (croppedImageType === 'image/png' && options) {
        // Prevent replacing transparent pixels for png images
        options.fillColor = undefined;
      }
      return this.imageCropper.getCroppedImage(croppedImageType, 'blob', .9, options)
        .then(result => result.blob);
    } else {
      return Promise.resolve(this.selectedFile);
    }
  }

}
