import { HttpEvent, HttpHandler, HttpInterceptor, HttpRequest } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Injectable } from '@angular/core';

/**
 * Adds an X-Logged-In-As header to every request that ensures the currently logged in user is the same as the currently shown dashboard
 * This might be different when you log in to another service in another tab
 */
@Injectable()
export class MainHttpInterceptor implements HttpInterceptor {
  static serviceEmail: string | null = null;

  intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    if (MainHttpInterceptor.serviceEmail) {
      req = req.clone({
        headers: req.headers.append('X-Logged-In-As', MainHttpInterceptor.serviceEmail),
      });
    }
    return next.handle(req);
  }
}

