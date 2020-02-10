import { ScrollingModule } from '@angular/cdk/scrolling';
import { NgModule } from '@angular/core';
import { MatSelectModule } from '@angular/material/select';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { MatToolbarModule } from '@angular/material/toolbar';
import { RouterModule, Routes } from '@angular/router';
import { EffectsModule } from '@ngrx/effects';
import { StoreModule } from '@ngrx/store';
import { SharedModule } from '../shared/shared.module';
import { EditIncidentComponent } from './components/edit-incident/edit-incident.component';
import { IncidentListComponent } from './components/incident-list/incident-list.component';
import { MapConfigComponent } from './components/map-config/map-config.component';
import { EditIncidentPageComponent } from './pages/edit-incident-page/edit-incident-page.component';
import { IncidentsPageComponent } from './pages/incidents-page/incidents-page.component';
import { IncidentsTabsPageComponent } from './pages/incidents-tabs-page/incidents-tabs-page.component';
import { IncidentStatus } from './pages/reports';
import { ReportsSettingsPageComponent } from './pages/reports-settings-page/reports-settings-page.component';
import { ReportsEffects } from './reports.effects';
import { reportsReducer } from './reports.reducer';

const routes: Routes = [
  { path: '', redirectTo: 'incidents', pathMatch: 'full' },
  {
    path: 'incidents', component: IncidentsTabsPageComponent, children: [
      { path: '', redirectTo: IncidentStatus.NEW, pathMatch: 'full' },
      { path: ':status', component: IncidentsPageComponent },
    ],
  },
  { path: 'incidents/detail/:id', component: EditIncidentPageComponent },
  { path: 'settings', component: ReportsSettingsPageComponent },
];

@NgModule({
  imports: [
    SharedModule,
    RouterModule.forChild(routes),
    StoreModule.forFeature('reports', reportsReducer),
    EffectsModule.forFeature([ReportsEffects]),
    MatToolbarModule,
    MatSelectModule,
    ScrollingModule,
    MatSnackBarModule,
    MatSlideToggleModule,
  ],
  exports: [],
  declarations: [
    IncidentsPageComponent,
    ReportsSettingsPageComponent,
    MapConfigComponent,
    IncidentListComponent,
    EditIncidentPageComponent,
    EditIncidentComponent,
    IncidentsTabsPageComponent,
  ],
})
export class ReportsModule {
}
