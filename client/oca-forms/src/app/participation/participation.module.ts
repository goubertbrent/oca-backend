import { NgModule } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatNativeDateModule } from '@angular/material/core';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MAT_FORM_FIELD_DEFAULT_OPTIONS, MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatListModule } from '@angular/material/list';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatTabsModule } from '@angular/material/tabs';
import { MatToolbarModule } from '@angular/material/toolbar';
import { RouterModule, Routes } from '@angular/router';
import { EffectsModule } from '@ngrx/effects';
import { StoreModule } from '@ngrx/store';
import { SharedModule } from '../shared/shared.module';
import { CitySettingsComponent } from './components/city-settings/city-settings.component';
import { ProjectDetailsComponent } from './components/project-details/project-details.component';
import { ProjectStatisticsComponent } from './components/project-statistics/project-statistics.component';
import { CitySettingsPageComponent } from './pages/city-settings-page/city-settings-page.component';
import { CreateProjectPageComponent } from './pages/create-project-page/create-project-page.component';
import { ParticipationMainPageComponent } from './pages/participation-main-page/participation-main-page.component';
import { ProjectDetailsPageComponent } from './pages/project-details-page/project-details-page.component';
import { ProjectListPageComponent } from './pages/project-list-page/project-list-page.component';
import { ParticipationEffects } from './participation.effects';
import { participationReducer } from './participation.reducer';


const routes: Routes = [
  {
    path: '', component: ParticipationMainPageComponent, children: [
      { path: '', redirectTo: 'projects', pathMatch: 'full' },
      { path: 'projects', component: ProjectListPageComponent },
      { path: 'projects/create', component: CreateProjectPageComponent },
      { path: 'projects/:id', component: ProjectDetailsPageComponent },
      { path: 'settings', component: CitySettingsPageComponent },
    ],
  },
];

@NgModule({
  imports: [
    RouterModule.forChild(routes),
    StoreModule.forFeature('psp', participationReducer),
    EffectsModule.forFeature([ ParticipationEffects ]),
    MatNativeDateModule,
    SharedModule,
    MatListModule,
    MatFormFieldModule,
    MatInputModule,
    MatDatepickerModule,
    MatButtonModule,
    MatTabsModule,
    MatToolbarModule,
    MatIconModule,
    MatSidenavModule,
  ],
  exports: [],
  declarations: [
    ProjectListPageComponent,
    ProjectDetailsPageComponent,
    ProjectDetailsComponent,
    CreateProjectPageComponent,
    CitySettingsComponent,
    ProjectStatisticsComponent,
    ParticipationMainPageComponent,
    CitySettingsPageComponent,
  ],
  providers: [ {
    provide: MAT_FORM_FIELD_DEFAULT_OPTIONS,
    useValue: {
      appearance: 'standard',
    },
  } ],
})
export class ParticipationModule {
}