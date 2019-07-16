export interface UploadedFile {
  id: number;
  content_type: string;
  size: number;
  url: string;
}

export interface UploadFormFileReference {
  type: 'form';
  id: number;
}

export type UploadFileReference = UploadFormFileReference;

export interface UploadFileDialogConfig {
  reference?: UploadFileReference;
  uploadPrefix: string;
  title: string;
  accept?: string;
  // https://github.com/fengyuanchen/cropperjs/blob/master/README.md#options
  cropOptions?: Cropper.Options;
  croppedCanvasOptions?: Cropper.GetCroppedCanvasOptions;
}
