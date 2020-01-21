import { Routes } from '@angular/router';

export const JCC_APPOINTMENTS_ROUTES: Routes = [
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
        loadChildren: () => import('./pages/appointments/jcc-appointments.module').then(m => m.JccAppointmentsModule),
      },
    ],
  },
  {
    path: 'new-appointment',
    children: [
      {
        path: '',
        loadChildren: () => import('./pages/new-appointment/jcc-new-appointment.module').then(m => m.JccNewAppointmentModule),
      },
    ],
  },
];
