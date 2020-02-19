import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { IonicModule } from '@ionic/angular';
import { EffectsModule } from '@ngrx/effects';
import { StoreModule } from '@ngrx/store';
import { TranslateModule } from '@ngx-translate/core';
import { eventsReducer } from './events-reducer';
import { EventsEffects } from './events.effects';
import { EVENTS_FEATURE } from './events.state';


export const EVENTS_ROUTES: Routes = [
  {
    path: '',
    children: [
      {
        path: '',
        loadChildren: () => import('./pages/events/events.module').then(m => m.EventsPageModule),
      },
      {
        path: ':eventId',
        loadChildren: () => import('./pages/event-details/event-details.module').then(m => m.EventDetailsPageModule),
      },
    ],
  },
];


@NgModule({
  declarations: [],
  imports: [
    IonicModule,
    RouterModule.forChild(EVENTS_ROUTES),
    EffectsModule.forFeature([EventsEffects]),
    StoreModule.forFeature(EVENTS_FEATURE, eventsReducer),
    TranslateModule,
  ],
})
export class EventsModule {
}
