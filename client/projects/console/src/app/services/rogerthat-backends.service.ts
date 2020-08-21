import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { map } from 'rxjs/operators';
import { EmbeddedApp, EmbeddedAppTag, FirebaseProject, PaymentProvider, SaveEmbeddedApp } from '../interfaces';
import { ConsoleConfig } from './console-config';

@Injectable()
export class RogerthatBackendsService {

  constructor(private http: HttpClient) {
  }

  getPaymentProviders() {
    return this.http.get <PaymentProvider[]>(`${ConsoleConfig.RT_API_URL}/payment/providers`);
  }

  createPaymentProvider(paymentProvider: PaymentProvider) {
    return this.http.post<PaymentProvider>(`${ConsoleConfig.RT_API_URL}/payment/providers`, paymentProvider);
  }

  getPaymentProvider(providerId: string) {
    return this.http.get<PaymentProvider>(`${ConsoleConfig.RT_API_URL}/payment/providers/${providerId}`);
  }

  updatePaymentProvider(paymentProvider: PaymentProvider) {
    const url = `${ConsoleConfig.RT_API_URL}/payment/providers/${paymentProvider.id}`;
    return this.http.put<PaymentProvider>(url, paymentProvider);
  }

  removePaymentProvider(paymentProvider: PaymentProvider) {
    const url = `${ConsoleConfig.RT_API_URL}/payment/providers/${paymentProvider.id}`;
    return this.http.delete<PaymentProvider>(url).pipe(
      map(() => paymentProvider),
    );
  }

  listEmbeddedApps(tag?: EmbeddedAppTag) {
    let params = new HttpParams();
    if (tag) {
      params = params.set('tag', tag);
    }
    return this.http.get<EmbeddedApp[]>(`${ConsoleConfig.RT_API_URL}/embedded-apps`, { params });
  }

  createEmbeddedApp(embeddedApp: SaveEmbeddedApp) {
    return this.http.post<EmbeddedApp>(`${ConsoleConfig.RT_API_URL}/embedded-apps`, embeddedApp);
  }

  getEmbeddedApp(embeddedAppName: string) {
    return this.http.get<EmbeddedApp>(`${ConsoleConfig.RT_API_URL}/embedded-apps/${embeddedAppName}`);
  }

  updateEmbeddedApp(embeddedApp: SaveEmbeddedApp) {
    return this.http.put<EmbeddedApp>(`${ConsoleConfig.RT_API_URL}/embedded-apps/${embeddedApp.name}`, embeddedApp);
  }

  removeEmbeddedApp(embeddedAppName: string) {
    return this.http.delete(`${ConsoleConfig.RT_API_URL}/embedded-apps/${embeddedAppName}`).pipe(
      map(() => embeddedAppName),
    );
  }

  listFirebaseProjects() {
    return this.http.get<FirebaseProject[]>(`${ConsoleConfig.RT_API_URL}/firebase-projects`);
  }

  createFirebaseProject(file: string) {
    return this.http.put<FirebaseProject>(`${ConsoleConfig.RT_API_URL}/firebase-projects`, { file: file });
  }
}
