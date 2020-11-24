import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';
import { MatToolbarModule } from '@angular/material/toolbar';
import { RouterModule, Routes } from '@angular/router';
import { EffectsModule } from '@ngrx/effects';
import { StoreModule } from '@ngrx/store';
import { SharedModule } from '../../../../../src/app/shared/shared.module';
import { MapConfigComponent } from './map-config/map-config.component';
import { MapsSettingsPageComponent } from './map-settings-page/maps-settings-page.component';
import { MapsEffects } from './maps.effects';
import { mapsFeatureKey, mapsReducer } from './maps.reducer';
import { MapAppListComponent } from './map-app-list/map-app-list.component';


const routes: Routes = [
  { path: '', component: MapAppListComponent },
  { path: ':appId', component: MapsSettingsPageComponent },
];


@NgModule({
  declarations: [
    MapsSettingsPageComponent,
    MapConfigComponent,
    MapAppListComponent,
  ],
  imports: [
    CommonModule,
    RouterModule.forChild(routes),
    StoreModule.forFeature(mapsFeatureKey, mapsReducer),
    EffectsModule.forFeature([MapsEffects]),
    MatToolbarModule,
    MatIconModule,
    MatButtonModule,
    MatProgressSpinnerModule,
    SharedModule,
    MatSelectModule,
  ],
})
export class MapsModule {
}
