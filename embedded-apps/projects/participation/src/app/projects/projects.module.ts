import { CommonModule, DatePipe } from '@angular/common';
import { HttpClientModule } from '@angular/common/http';
import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterModule, Routes } from '@angular/router';
import { IonicModule } from '@ionic/angular';
import { EffectsModule } from '@ngrx/effects';
import { StoreModule } from '@ngrx/store';
import { TranslateModule } from '@ngx-translate/core';
import { JoyrideModule } from 'ngx-joyride';
import { MerchantListComponent } from './components/merchant-list/merchant-list.component';
import { ProjectCardComponent } from './components/project-card/project-card.component';
import { HomePageComponent } from './pages/home-page/home-page.component';
import { InfoPageComponent } from './pages/info-page/info-page.component';
import { MerchantDetailPageComponent } from './pages/merchant-detail-page/merchant-detail-page.component';
import { MerchantListPageComponent } from './pages/merchant-list-page/merchant-list-page.component';
import { ProjectDetailsPageComponent } from './pages/project-details-page/project-details-page.component';
import { ProjectsPageComponent } from './pages/projects-page/projects-page.component';
import { MarkdownPipe } from './pipes/markdown.pipe';
import { ProjectsEffects } from './projects.effects';
import { projectsReducer } from './projects.reducer';


const routes: Routes = [
  { path: '', redirectTo: 'psp', pathMatch: 'full' },
  {
    path: 'psp',
    component: HomePageComponent,
    children: [
      { path: '', redirectTo: 'overview', pathMatch: 'full' },
      { path: 'overview', component: ProjectsPageComponent },
      { path: 'merchants', component: MerchantListPageComponent },
      { path: 'info', component: InfoPageComponent } ],
  },
  { path: 'psp/overview/:id', component: ProjectDetailsPageComponent },
  { path: 'psp/merchants/:id', component: MerchantDetailPageComponent },
];

@NgModule({
  declarations: [
    ProjectCardComponent,
    MerchantListPageComponent,
    ProjectsPageComponent,
    MerchantListComponent,
    HomePageComponent,
    ProjectDetailsPageComponent,
    InfoPageComponent,
    MerchantDetailPageComponent,
    MarkdownPipe,
  ],
  imports: [
    IonicModule,
    CommonModule,
    FormsModule,
    HttpClientModule,
    RouterModule.forChild(routes),
    EffectsModule.forFeature([ ProjectsEffects ]),
    StoreModule.forFeature('projects', projectsReducer),
    TranslateModule,
    JoyrideModule.forRoot(),
  ],
  providers: [
    DatePipe,
  ],
})
export class ProjectsModule {
}
