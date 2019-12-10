import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

const routes: Routes = [
  { path: '', redirectTo: 'scripts', pathMatch: 'full' },
  {
    path: 'scripts',
    loadChildren: () => import('./interactive-explorer/explorer.module').then(m => m.ExplorerModule),
  }];

@NgModule({
  imports: [
    CommonModule,
    RouterModule.forChild(routes),
  ],
})
export class AdminModule {
}
