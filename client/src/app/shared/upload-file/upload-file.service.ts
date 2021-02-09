import { HttpClient, HttpEvent, HttpParams, HttpRequest } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { MediaType } from '@oca/web-shared';
import { Observable } from 'rxjs';
import { GalleryFile, UploadedFile, UploadFileReference } from './file-upload';

@Injectable({ providedIn: 'root' })
export class UploadFileService {

  constructor(private http: HttpClient) {
  }

  getFiles(mediaType: MediaType, prefix?: string, reference?: UploadFileReference) {
    let params = new HttpParams();
    params = params.set('media_type', mediaType);
    if (prefix) {
      params = params.set('prefix', prefix);
    }
    if (reference) {
      params = params.set('reference_type', reference.type);
      if ('id' in reference) {
        params = params.set('reference', reference.id.toString());
      }
    }
    return this.http.get<UploadedFile[]>(`/common/files`, { params });
  }

  uploadImage(image: Blob, prefix: string, type: MediaType, reference?: UploadFileReference): Observable<HttpEvent<UploadedFile>> {
    const data = new FormData();
    data.append('file', image);
    data.append('type', type);
    if (reference) {
      data.append('reference_type', reference.type);
      if ('id' in reference) {
        data.append('reference', reference.id.toString());
      }
    }
    return this.http.request(new HttpRequest('POST', `/common/files/${prefix}`, data, { reportProgress: true }));
  }

  getGalleryFiles(prefix: 'logo' | 'avatar') {
    return this.http.get<GalleryFile[]>(`/common/image-gallery/${prefix}`);
  }
}
