import { HttpEventType } from '@angular/common/http';
import { ChangeDetectionStrategy, ChangeDetectorRef, Component, Inject, OnDestroy, ViewChild } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { ProgressSpinnerMode } from '@angular/material/progress-spinner';
import { TranslateService } from '@ngx-translate/core';
import Cropper from 'cropperjs';
import { Observable, Subject } from 'rxjs';
import { takeUntil, tap } from 'rxjs/operators';
import { FormsService } from '../../forms.service';
import { UploadedFile, UploadedFormFile } from '../../interfaces/forms';
import { ImageCropperComponent } from '../image-cropper/image-cropper.component';

export interface UploadImageDialogConfig {
  accept?: string;
  // https://github.com/fengyuanchen/cropperjs/blob/master/README.md#options
  cropOptions?: Cropper.Options;
  croppedCanvasOptions?: Cropper.GetCroppedCanvasOptions;
  formId: number;
  title: string;
}

@Component({
  selector: 'oca-upload-image-dialog',
  templateUrl: './upload-image-dialog.component.html',
  styleUrls: [ './upload-image-dialog.component.scss' ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class UploadImageDialogComponent implements OnDestroy {
  @ViewChild(ImageCropperComponent, { static: false }) imageCropper: ImageCropperComponent;

  selectedTabIndex = 1;
  selectedImageUrl: string;
  showProgress = false;
  uploadPercent = 0;
  progressMode: ProgressSpinnerMode = 'indeterminate';
  uploadError: string | null = null;
  images$: Observable<UploadedFile[]>;

  private _destroyed = new Subject();


  constructor(@Inject(MAT_DIALOG_DATA) public data: UploadImageDialogConfig,
              private _dialogRef: MatDialogRef<UploadImageDialogComponent>,
              private _changeDetectorRef: ChangeDetectorRef,
              private _formsService: FormsService,
              private _translate: TranslateService) {
    this.images$ = this._formsService.getImages().pipe(tap(results => {
      if (results.length === 0) {
        this.selectedTabIndex = 0;
      }
    }));
    data.accept = data.accept || 'image/png,image/jpeg';
    data.cropOptions = {
      aspectRatio: 16 / 6,
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

  imagePicked(image: UploadedFile) {
    this._dialogRef.close(image.url);
  }

  onFileSelected(event: Event) {
    this.showProgress = true;
    this.progressMode = 'indeterminate';
    const reader = new FileReader();
    const target = event.target as HTMLInputElement;
    if (target.files && target.files.length) {
      const file = target.files[ 0 ];
      reader.readAsDataURL(file);
      reader.onload = () => {
        this.selectedImageUrl = reader.result as string;
        this.showProgress = false;
        this._changeDetectorRef.markForCheck();
      };
    }
  }

  ngOnDestroy(): void {
    this._destroyed.next();
    this._destroyed.complete();
  }

  save() {
    this.showProgress = true;
    this.progressMode = 'indeterminate';
    this.uploadError = null;
    this.imageCropper.getCroppedImage('blob', .9, this.data.croppedCanvasOptions).then(croppedImage => {
      this.progressMode = 'determinate';
      this._changeDetectorRef.markForCheck();
      if (!croppedImage.blob) {
        return;
      }
      this._formsService.uploadImage(this.data.formId, croppedImage.blob).pipe(takeUntil(this._destroyed)).subscribe(event => {
        switch (event.type) {
          case HttpEventType.UploadProgress:
            this.uploadPercent = (100 * event.loaded) / (event.total as number);
            break;
          case HttpEventType.Response:
            this.showProgress = false;
            const body: UploadedFormFile = event.body as UploadedFormFile;
            this._dialogRef.close(body.url);
            break;
        }
        this._changeDetectorRef.markForCheck();
      }, e => this.handleUploadError(e));
    });
  }

  handleUploadError(error: any) {
    this.uploadPercent = 0;
    this.showProgress = false;
    this.uploadError = this._translate.instant('oca.upload_error_check_internet');
    this._changeDetectorRef.markForCheck();
  }

}
