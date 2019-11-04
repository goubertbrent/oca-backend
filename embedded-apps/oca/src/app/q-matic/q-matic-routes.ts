import { Routes } from '@angular/router';

export const Q_MATIC_ROUTES: Routes = [
  {
    path: '',
    redirectTo: 'appointments',
    pathMatch: 'full',
  },
  {
    path: 'appointments',
    children: [
      {
        path: '',
        loadChildren: () => import('./pages/appointments/appointments.module').then(m => m.AppointmentsModule),
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
