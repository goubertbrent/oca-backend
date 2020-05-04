import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatPaginatorModule } from '@angular/material/paginator';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatTableModule } from '@angular/material/table';
import { MatTabsModule } from '@angular/material/tabs';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { RouterModule, Routes } from '@angular/router';
import { EffectsModule } from '@ngrx/effects';
import { StoreModule } from '@ngrx/store';
import { TranslateModule } from '@ngx-translate/core';
import { MAT_PAGINATOR_INTL_PROVIDER } from '../shared/i18n/material-components';
import { VouchersPageComponent } from './vouchers-page/vouchers-page.component';
import { VouchersEffects } from './vouchers.effects';
import { vouchersFeatureKey, vouchersReducer } from './vouchers.reducer';


const routes: Routes = [
  { path: '', component: VouchersPageComponent },
];


@NgModule({
  declarations: [VouchersPageComponent],
  imports: [
    CommonModule,
    EffectsModule.forFeature([VouchersEffects]),
    StoreModule.forFeature(vouchersFeatureKey, vouchersReducer),
    TranslateModule,
    RouterModule.forChild(routes),
    MatTabsModule,
    MatTableModule,
    MatSlideToggleModule,
    MatProgressBarModule,
    MatPaginatorModule,
    MatToolbarModule,
    MatButtonModule,
    MatIconModule,
    MatTooltipModule,
  ],
  providers: [MAT_PAGINATOR_INTL_PROVIDER],
})
export class VouchersModule {
}
