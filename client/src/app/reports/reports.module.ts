import { ScrollingModule } from '@angular/cdk/scrolling';
import { NgModule } from '@angular/core';
import { MAT_FORM_FIELD_DEFAULT_OPTIONS } from '@angular/material/form-field';
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
import { ReportsSettingsPageComponent } from './pages/reports-settings-page/reports-settings-page.component';
import { ReportsEffects } from './reports.effects';
import { reportsReducer } from './reports.reducer';

const routes: Routes = [
  { path: '', redirectTo: 'incidents', pathMatch: 'full' },
  { path: 'incidents', component: IncidentsPageComponent },
  { path: 'incidents/:id', component: EditIncidentPageComponent },
  { path: 'settings', component: ReportsSettingsPageComponent },
];

@NgModule({
  imports: [
    SharedModule,
    RouterModule.forChild(routes),
    StoreModule.forFeature('reports', reportsReducer),
    EffectsModule.forFeature([ReportsEffects]),
    MatToolbarModule,
    MatSnackBarModule,
    MatSelectModule,
    ScrollingModule,
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
  ],
  providers: [
    { provide: MAT_FORM_FIELD_DEFAULT_OPTIONS, useValue: { appearance: 'standard' } },
  ],
})
export class ReportsModule {
}
