import { ChangeDetectionStrategy, Component, ElementRef, EventEmitter, Input, Output, ViewChild, ViewEncapsulation } from '@angular/core';
import Cropper from 'cropperjs';

export interface ImageCropperResult {
  imageData: Cropper.ImageData;
  cropData: Cropper.CropBoxData;
  blob: Blob | null;
  dataUrl: string | null;
}

@Component({
  selector: 'oca-image-cropper',
  templateUrl: './image-cropper.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
})
export class ImageCropperComponent {
  @ViewChild('image') image: ElementRef<HTMLImageElement>;

  @Input() imageUrl: any;
  @Input() cropperOptions: Cropper.Options = {};

  @Output() ready = new EventEmitter();

  public cropper: Cropper;

  constructor() {
  }

  imageLoaded() {
    this.ready.emit(true);
    if (this.cropper) {
      this.cropper.destroy();
    }
    this.cropper = new Cropper(this.image.nativeElement, this.cropperOptions);
  }

  getCroppedImage(type: 'blob' | 'base64', quality: number, options?: Cropper.GetCroppedCanvasOptions): Promise<ImageCropperResult> {
    const imageData = this.cropper.getImageData();
    const cropData = this.cropper.getCropBoxData();
    const canvas = this.cropper.getCroppedCanvas(options);
    const data: ImageCropperResult = { imageData, cropData, blob: null, dataUrl: null };
    const imageType = 'image/jpeg';

    return new Promise(resolve => {
      if (type === 'base64') {
        resolve({ ...data, dataUrl: canvas.toDataURL(imageType, quality) });
      } else {
        canvas.toBlob(blob => resolve({ ...data, blob }), imageType, quality);
      }
    });
  }
}
