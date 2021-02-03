import { MediaType } from '@oca/web-shared';

export interface MediaItem {
  type: MediaType;
  content: string;
  thumbnail_url: string | null;
  file_reference: string | null;
}
