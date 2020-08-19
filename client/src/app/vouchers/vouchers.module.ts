import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatDialogModule } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatSortModule } from '@angular/material/sort';
import { MatTableModule } from '@angular/material/table';
import { MatTabsModule } from '@angular/material/tabs';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { RouterModule, Routes } from '@angular/router';
import { EffectsModule } from '@ngrx/effects';
import { StoreModule } from '@ngrx/store';
import { TranslateModule } from '@ngx-translate/core';
import { ERROR_HANDLING_TRANLATIONS_PROVIDER } from '../../environments/config';
import { MAT_PAGINATOR_INTL_PROVIDER } from '../shared/i18n/material-components';
import { CirkloSettingsPageComponent } from './cirklo-settings-page/cirklo-settings-page.component';
import { VouchersPageComponent } from './vouchers-page/vouchers-page.component';
import { WhitelistDialogComponent } from './vouchers-page/whitelist-dialog.component';
import { VouchersEffects } from './vouchers.effects';
import { vouchersFeatureKey, vouchersReducer } from './vouchers.reducer';

const routes: Routes = [
  { path: '', component: VouchersPageComponent },
  { path: 'settings', component: CirkloSettingsPageComponent },
];


@NgModule({
  declarations: [VouchersPageComponent, CirkloSettingsPageComponent, WhitelistDialogComponent],
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
    MatToolbarModule,
    MatButtonModule,
    MatDialogModule,
    MatIconModule,
    MatTooltipModule,
    MatSortModule,
    ReactiveFormsModule,
    MatFormFieldModule,
    MatInputModule,
  ],
  providers: [
    MAT_PAGINATOR_INTL_PROVIDER,
    ERROR_HANDLING_TRANLATIONS_PROVIDER,
  ],
})
export class VouchersModule {
}
