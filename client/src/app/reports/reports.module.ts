import { ScrollingModule } from '@angular/cdk/scrolling';
import { NgModule } from '@angular/core';
import { MatSelectModule } from '@angular/material/select';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { MatToolbarModule } from '@angular/material/toolbar';
import { RouterModule, Routes } from '@angular/router';
import { EffectsModule } from '@ngrx/effects';
import { StoreModule } from '@ngrx/store';
import { MarkdownModule } from '@oca/web-shared';
import { ERROR_HANDLING_TRANLATIONS_PROVIDER } from '../../environments/config';
import { SharedModule } from '../shared/shared.module';
import { EditIncidentComponent } from './components/edit-incident/edit-incident.component';
import { IncidentListComponent } from './components/incident-list/incident-list.component';
import { EditIncidentPageComponent } from './pages/edit-incident-page/edit-incident-page.component';
import { IncidentsPageComponent } from './pages/incidents-page/incidents-page.component';
import { IncidentsTabsPageComponent } from './pages/incidents-tabs-page/incidents-tabs-page.component';
import { IncidentStatus } from './pages/reports';
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
    MarkdownModule,
  ],
  exports: [],
  declarations: [
    IncidentsPageComponent,
    IncidentListComponent,
    EditIncidentPageComponent,
    EditIncidentComponent,
    IncidentsTabsPageComponent,
  ],
  providers: [ERROR_HANDLING_TRANLATIONS_PROVIDER],
})
export class ReportsModule {
}
