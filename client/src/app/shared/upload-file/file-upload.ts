export interface GcsFile {
  content_type: string;
  size: number;
  url: string;
}

export interface UploadedFile extends GcsFile {
  id: number;
}

export interface UploadFormFileReference {
  type: 'form';
  id: number;
}

export interface UploadFormFileBrandingSettings {
  type: 'branding_settings';
}

export interface UploadEventFileReference {
  type: 'event';
  id: number;
}

export type UploadFileReference = UploadFormFileReference | UploadEventFileReference | UploadFormFileBrandingSettings;

export interface UploadFileDialogConfig {
  reference?: UploadFileReference;
  // Set to 'image' to only allow uploading images
  fileType?: 'image';
  croppedImageType?: 'image/jpeg' | 'image/png';
  uploadPrefix: string;
  title: string;
  accept?: string;
  // https://github.com/fengyuanchen/cropperjs/blob/master/README.md#options
  cropOptions?: Cropper.Options;
  croppedCanvasOptions?: Cropper.GetCroppedCanvasOptions;
  /**
   * When set, the list of images you're able to choose will be limited to files with this path prefix
   */
  listPrefix?: string;
  gallery?: {
    prefix: 'logo' | 'avatar';
  };
}
