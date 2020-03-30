import { HttpEvent, HttpHandler, HttpInterceptor, HttpRequest } from '@angular/common/http';
import { Observable } from 'rxjs';

export class MainHttpInterceptor implements HttpInterceptor {
  static serviceEmail: string | null = null;

  intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    if (MainHttpInterceptor.serviceEmail) {
      req = req.clone({
        headers: req.headers.append('X-Logged-In-As', MainHttpInterceptor.serviceEmail),
      });
    } else {
      console.warn('MainHttpInterceptor.serviceEmail is not set');
    }
    return next.handle(req);
  }
}

