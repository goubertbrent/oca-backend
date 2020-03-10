import { HttpClient, HttpEvent, HttpParams, HttpRequest } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { GcsFile, UploadedFile, UploadFileReference } from './file-upload';

@Injectable({ providedIn: 'root' })
export class UploadFileService {

  constructor(private http: HttpClient) {
  }

  getFiles(prefix?: string) {
    let params = new HttpParams();
    if (prefix) {
      params = params.set('prefix', prefix);
    }
    return this.http.get<GcsFile[]>(`/common/files`, { params });
  }

  uploadImage(image: Blob, prefix: string, reference?: UploadFileReference): Observable<HttpEvent<UploadedFile>> {
    const data = new FormData();
    data.append('file', image);
    if (reference) {
      data.append('reference_type', reference.type);
      if ('id' in reference) {
        data.append('reference', reference.id.toString());
      }
    }
    return this.http.request(new HttpRequest('POST', `/common/files/${prefix}`, data, { reportProgress: true }));
  }

  getGalleryFiles(prefix: 'logo' | 'avatar') {
    return this.http.get<GcsFile[]>(`/common/image-gallery/${prefix}`);
  }
}
