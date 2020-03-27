import { ChangeDetectionStrategy, Component, ElementRef, EventEmitter, Input, Output, ViewChild } from '@angular/core';
import Cropper from 'cropperjs';
import ViewMode = Cropper.ViewMode;

export interface ImageCropperResult {
  imageData: Cropper.ImageData;
  cropData: Cropper.CropBoxData;
  blob: Blob | null;
  dataUrl: string | null;
}

@Component({
  selector: 'oca-image-cropper',
  templateUrl: './image-cropper.component.html',
  styleUrls: ['./image-cropper.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ImageCropperComponent {
  @ViewChild('image', { static: true }) image: ElementRef<HTMLImageElement>;

  @Input() imageUrl: any;
  @Input() cropperOptions: Cropper.Options = {};

  @Output() ready = new EventEmitter();

  public cropper: Cropper;
  selectedViewMode: ViewMode;
  isImageLoaded = false;

  constructor() {
  }

  imageLoaded() {
    this.ready.emit(true);
    if (this.cropper) {
      this.cropper.destroy();
    }
    this.selectedViewMode = this.cropperOptions.viewMode ?? 1;
    this.cropper = new Cropper(this.image.nativeElement, this.cropperOptions);
    this.isImageLoaded = true;
  }

  setViewMode(viewMode: ViewMode) {
    this.cropper.destroy();
    this.cropperOptions = { ...this.cropperOptions, viewMode };
    this.cropper = new Cropper(this.image.nativeElement, this.cropperOptions);
  }

  getCroppedImage(imageType: 'image/png' | 'image/jpeg', type: 'blob' | 'base64', quality: number,
                  options?: Cropper.GetCroppedCanvasOptions): Promise<ImageCropperResult> {
    const imageData = this.cropper.getImageData();
    const cropData = this.cropper.getCropBoxData();
    const canvas = this.cropper.getCroppedCanvas(options);
    const data: ImageCropperResult = { imageData, cropData, blob: null, dataUrl: null };

    return new Promise(resolve => {
      if (type === 'base64') {
        resolve({ ...data, dataUrl: canvas.toDataURL(imageType, quality) });
      } else if ('toBlob' in canvas) {
        canvas.toBlob(blob => resolve({ ...data, blob }), imageType, quality);
      } else {
          // Welcome to Edge.
          // TypeScript thinks `canvas` is 'never', so it needs casting.
          const dataUrl = (canvas as HTMLCanvasElement).toDataURL(type, quality);
          const result = /data:([^;]+);base64,(.*)$/.exec(dataUrl);

          if (!result) {
            throw Error('Data URL reading failed');
          }

          const outputType = result[1];
          const binaryStr = atob(result[2]);
          const d = new Uint8Array(binaryStr.length);

          for (let i = 0; i < d.length; i += 1) {
            d[i] = binaryStr.charCodeAt(i);
          }

          const blob = new Blob([d], { type: outputType });
          resolve({ ...data, blob});
      }
    });
  }
}
