import { Injectable } from '@angular/core';
import { ActivatedRouteSnapshot, CanActivate, RouterStateSnapshot, Routes, UrlTree } from '@angular/router';
import { Platform } from '@ionic/angular';
import { Observable } from 'rxjs';
import { AppointmentsPage } from './pages/appointments/appointments.page';

@Injectable()
class CanActivateRoute implements CanActivate {

  constructor(private platform: Platform) {
  }

  canActivate(route: ActivatedRouteSnapshot, routerStateSnapshot: RouterStateSnapshot): Observable<boolean | UrlTree> |
    Promise<boolean | UrlTree> | boolean | UrlTree {
    return this.platform.ready().then(() => true);
  }

}

export const Q_MATIC_ROUTES: Routes = [
  {
    canActivate: [CanActivateRoute],
    path: '',
    redirectTo: 'appointments',
    pathMatch: 'full',
  },
  {
    path: 'appointments',
    children: [
      {
        path: '',
        component: AppointmentsPage,
      },
    ],
  },
  {
    path: 'new-appointment',
    children: [
      {
        path: '',
        loadChildren: () => import('./pages/new-appointment/new-appointment.module').then(m => m.NewAppointmentModule),
      },
    ],
  },
];
