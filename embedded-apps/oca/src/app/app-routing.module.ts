import { NgModule } from '@angular/core';
import { PreloadAllModules, RouterModule, Routes } from '@angular/router';

const routes: Routes = [
  {
    path: 'q-matic',
    loadChildren: () => import('./q-matic/q-matic.module').then(m => m.QMaticModule),
  },
  {
    path: 'jcc-appointments',
    loadChildren: () => import('./jcc-appointments/jcc-appointments.module').then(m => m.JccAppointmentsModule),
  },
  {
    path: 'events',
    loadChildren: () => import('./events/events.module').then(m => m.EventsModule),
  },
  {
    path: 'cirklo',
    loadChildren: () => import('./cirklo/cirklo.module').then(m => m.CirkloModule),
  },
];

@NgModule({
  imports: [
    RouterModule.forRoot(routes, { preloadingStrategy: PreloadAllModules }),
  ],
  exports: [RouterModule],
})
export class AppRoutingModule {
}
