import { HttpEventType } from '@angular/common/http';
import { ChangeDetectionStrategy, ChangeDetectorRef, Component, Inject, OnDestroy, ViewChild } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef, ProgressSpinnerMode } from '@angular/material';
import { TranslateService } from '@ngx-translate/core';
import Cropper from 'cropperjs';
import { Observable, Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { FormsService } from '../../forms/forms.service';
import { NewsService } from '../../news/news.service';
import { ImageCropperComponent } from '../image-cropper/image-cropper.component';
import { UploadedFile } from '../images';

export interface UploadImageDialogConfig {
  type: 'form' | 'news';
  data?: any;
  title: string;
}

@Component({
  selector: 'oca-upload-image-dialog',
  templateUrl: './upload-image-dialog.component.html',
  styleUrls: [ './upload-image-dialog.component.scss' ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class UploadImageDialogComponent implements OnDestroy {
  @ViewChild(ImageCropperComponent) imageCropper: ImageCropperComponent;
  accept = 'image/png, image/jpeg';
  // https://github.com/fengyuanchen/cropperjs/blob/master/README.md#options
  cropOptions: Cropper.Options = {
    aspectRatio: 16 / 6,
    viewMode: 1,
    autoCropArea: 1,
  };

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
              private _newsService: NewsService,
              private _translate: TranslateService) {
    // TOOD move to shared service
    this.images$ = this._formsService.getImages();
  }

  imagePicked(image: UploadedFile) {
    this._dialogRef.close(image);
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
    const options: Cropper.GetCroppedCanvasOptions = {
      maxWidth: 1440,
      fillColor: '#ffffff',
    };
    this.showProgress = true;
    this.progressMode = 'indeterminate';
    this.uploadError = null;
    this.imageCropper.getCroppedImage('blob', .9, options).then(croppedImage => {
      this.progressMode = 'determinate';
      this._changeDetectorRef.markForCheck();
      if (!croppedImage.blob) {
        return;
      }
      let method;
      if (this.data.type === 'form') {
        method = this._formsService.uploadImage(this.data.data, croppedImage.blob);
      } else if (this.data.type === 'news') {
        method = this._newsService.uploadImage(croppedImage.blob);
      } else {
        throw new Error('Invalid data type ' + this.data.type);
      }
      method.pipe(takeUntil(this._destroyed)).subscribe(event => {
        switch (event.type) {
          case HttpEventType.UploadProgress:
            this.uploadPercent = (100 * event.loaded) / (event.total as number);
            break;
          case HttpEventType.Response:
            this.showProgress = false;
            const body: UploadedFile = event.body as UploadedFile;
            this._dialogRef.close(body);
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
