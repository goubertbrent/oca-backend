import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterModule, Routes } from '@angular/router';
import { IonicModule } from '@ionic/angular';
import { EffectsModule } from '@ngrx/effects';
import { StoreModule } from '@ngrx/store';
import { TranslateModule } from '@ngx-translate/core';
import { QRCodeModule } from 'angularx-qrcode';
import { environment } from '../../environments/environment';
import { BackButtonModule } from '../shared/back-button/back-button.module';
import { MarkdownModule } from '../shared/markdown/markdown.module';
import { CirkloEffects } from './cirklo.effects';
import { cirkloFeatureKey, cirkloReducer } from './cirklo.reducer';
import { LargeVoucherComponent } from './components/large-voucher/large-voucher.component';
import { SmallVoucherComponent } from './components/small-voucher/small-voucher.component';
import { VoucherIntroComponent } from './components/voucher-intro/voucher-intro.component';
import { CirkloHomePage } from './pages/cirklo-home/cirklo-home.page';
import { InfoPageComponent } from './pages/info-page/info-page.component';
import { MerchantDetailsPageComponent } from './pages/merchant-details-page/merchant-details-page.component';
import { MerchantsPageComponent } from './pages/merchants-page/merchants-page.component';
import { VoucherDetailsPageComponent } from './pages/voucher-details-page/voucher-details-page.component';
import { VoucherTransactionsPageComponent } from './pages/voucher-transactions-page/voucher-transactions-page.component';
import { VouchersPageComponent } from './pages/vouchers-page/vouchers-page.component';
import { MerchantAddressUrlPipe } from './merchant-address-url.pipe';

const routes: Routes = [
  {
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
  ],
  imports: [
    CommonModule,
    EffectsModule.forFeature([CirkloEffects, ...environment.cirkloExtraEffects]),
    FormsModule,
    IonicModule,
    RouterModule.forChild(routes),
    StoreModule.forFeature(cirkloFeatureKey, cirkloReducer),
    TranslateModule,
    BackButtonModule,
    QRCodeModule,
    MarkdownModule,
  ],
})
export class CirkloModule {
}
