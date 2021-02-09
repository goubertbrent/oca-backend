import { MediaType } from '@oca/web-shared';

export interface GalleryFile {
  content_type: string;
  size: number;
  url: string;
  thumbnail_url: string | null;
  type: MediaType;
}

export interface UploadedFile extends GalleryFile {
  id: string;
  title?: string | null;
}

export function isUploadedFile(item: UploadedFile | GalleryFile): item is UploadedFile {
  return 'id' in item;
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

export interface UploadPointOfInterestFileReference {
  type: 'point_of_interest';
  id: number;
}

export type UploadFileReference =
  UploadFormFileReference
  | UploadEventFileReference
  | UploadFormFileBrandingSettings
  | UploadPointOfInterestFileReference;

export interface UploadFileDialogConfig {
  reference?: UploadFileReference;
  // Set to 'image' to only allow uploading images
  croppedImageType?: 'image/jpeg' | 'image/png';
  uploadPrefix: string;
  mediaType?: MediaType;
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
