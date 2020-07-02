import { CommonModule } from '@angular/common';
import { HttpClient, HttpClientModule } from '@angular/common/http';
import { Injectable, NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { BrowserModule } from '@angular/platform-browser';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import {
  ActivatedRouteSnapshot,
  CanActivate,
  RouteReuseStrategy,
  RouterModule,
  RouterStateSnapshot,
  Routes,
  UrlTree,
} from '@angular/router';
import { SplashScreen } from '@ionic-native/splash-screen/ngx';
import { StatusBar } from '@ionic-native/status-bar/ngx';
import { IonicModule, IonicRouteStrategy, Platform } from '@ionic/angular';
import { EffectsModule } from '@ngrx/effects';
import { StoreModule } from '@ngrx/store';
import { MissingTranslationHandler, TranslateLoader, TranslateModule } from '@ngx-translate/core';
import { RogerthatEffects } from '@oca/rogerthat';
import { BackButtonModule, CUSTOM_LOCALE_PROVIDER, HttpLoaderFactory, MarkdownModule, MissingTranslationWarnHandler } from '@oca/shared';
import { QRCodeModule } from 'angularx-qrcode';
import { Observable } from 'rxjs';
import { environment } from '../environments/environment';
import { CirkloAppComponent } from './cirklo-app.component';
import { cirkloAppReducers } from './cirklo.reducer';
import { LargeVoucherComponent } from './components/large-voucher/large-voucher.component';
import { SmallVoucherComponent } from './components/small-voucher/small-voucher.component';
import { VoucherIntroComponent } from './components/voucher-intro/voucher-intro.component';
import { MerchantAddressUrlPipe } from './merchant-address-url.pipe';
import { CirkloHomePage } from './pages/cirklo-home/cirklo-home.page';
import { InfoPageComponent } from './pages/info-page/info-page.component';
import { MerchantDetailsPageComponent } from './pages/merchant-details-page/merchant-details-page.component';
import { MerchantsPageComponent } from './pages/merchants-page/merchants-page.component';
import { VoucherDetailsPageComponent } from './pages/voucher-details-page/voucher-details-page.component';
import { VoucherTransactionsPageComponent } from './pages/voucher-transactions-page/voucher-transactions-page.component';
import { VouchersPageComponent } from './pages/vouchers-page/vouchers-page.component';
import { VoucherQrDataPipe } from './voucher-qr-data.pipe';

@Injectable()
class CanActivateRoute implements CanActivate {

  constructor(private platform: Platform) {
  }

  canActivate(route: ActivatedRouteSnapshot, state: RouterStateSnapshot): Observable<boolean | UrlTree> |
    Promise<boolean | UrlTree> | boolean | UrlTree {
    return this.platform.ready().then(() => true);
  }

}

const routes: Routes = [
  {
    canActivate: [CanActivateRoute],
    path: '',
    component: CirkloHomePage,
    children: [
      { path: '', redirectTo: 'vouchers', pathMatch: 'full' },
      { path: 'vouchers', component: VouchersPageComponent },
      { path: 'vouchers/:id', component: VoucherDetailsPageComponent },
      { path: 'vouchers/:id/transactions', component: VoucherTransactionsPageComponent },
      { path: 'merchants', component: MerchantsPageComponent },
      { path: 'merchants/:id', component: MerchantDetailsPageComponent },
      { path: 'info', component: InfoPageComponent },
    ],
  },
];

@NgModule({
  declarations: [
    CirkloAppComponent,
    CirkloHomePage,
    LargeVoucherComponent,
    SmallVoucherComponent,
    VoucherIntroComponent,
    VouchersPageComponent,
    VoucherDetailsPageComponent,
    VoucherTransactionsPageComponent,
    MerchantsPageComponent,
    MerchantDetailsPageComponent,
    InfoPageComponent,
    MerchantAddressUrlPipe,
    VoucherQrDataPipe,
  ],
  imports: [
    BrowserModule,
    BrowserAnimationsModule, // Required for @angular/material
    CommonModule,
    IonicModule.forRoot(environment.production ? {} : { mode: Math.random() > .5 ? 'ios' : 'md' }),
    HttpClientModule,
    TranslateModule.forRoot({
      loader: {
        provide: TranslateLoader,
        useFactory: HttpLoaderFactory,
        deps: [HttpClient],
      },
      missingTranslationHandler: {
        provide: MissingTranslationHandler,
        useClass: MissingTranslationWarnHandler,
      },
    }),
    StoreModule.forRoot(cirkloAppReducers, {
      runtimeChecks: {
        strictActionWithinNgZone: true,
        strictStateImmutability: true,
        strictActionImmutability: true,
        strictStateSerializability: true,
        strictActionSerializability: true,
      },
    }),
    EffectsModule.forRoot([RogerthatEffects, ...environment.ngrxEffects]),
    FormsModule,
    IonicModule,
    RouterModule.forRoot(routes),
    TranslateModule,
    BackButtonModule,
    QRCodeModule,
    MarkdownModule,
  ],
  providers: [
    CanActivateRoute,
    StatusBar,
    SplashScreen,
    CUSTOM_LOCALE_PROVIDER,
    { provide: RouteReuseStrategy, useClass: IonicRouteStrategy },
  ],
  bootstrap: [CirkloAppComponent],
})
export class CirkloModule {
}
