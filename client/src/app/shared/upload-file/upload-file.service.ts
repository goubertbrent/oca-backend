import { HttpClient, HttpEvent, HttpRequest } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { UploadedFile, UploadFileReference } from './file-upload';

@Injectable({ providedIn: 'root' })
export class UploadFileService {

  constructor(private http: HttpClient) {
  }

  getFiles() {
    return this.http.get<UploadedFile[]>(`/common/files`);
  }

  uploadImage(image: Blob, prefix: string, reference?: UploadFileReference): Observable<HttpEvent<UploadedFile>> {
    const data = new FormData();
    data.append('file', image);
    if (reference) {
      data.append('reference_type', reference.type);
      data.append('reference', reference.id.toString());
    }
    return this.http.request(new HttpRequest('POST', `/common/files/${prefix}`, data, { reportProgress: true }));
  }

}
