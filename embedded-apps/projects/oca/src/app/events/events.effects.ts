import { Injectable } from '@angular/core';
import { Router } from '@angular/router';
import { AlertController } from '@ionic/angular';
import { Actions, Effect, ofType } from '@ngrx/effects';
import { Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { RogerthatService } from '@oca/rogerthat';
import { of } from 'rxjs';
import { catchError, map, switchMap, tap } from 'rxjs/operators';
import { ErrorService } from '../error.service';
import { AppState } from '../reducers';
import { EventAnnouncementList, OcaEventList } from './events';
import {
  AddEventToCalendarAction,
  AddEventToCalendarFailedAction,
  AddEventToCalendarSuccessAction,
  EventsActions,
  EventsActionTypes,
  GetAnnouncementsAction,
  GetAnnouncementsFailedAction,
  GetAnnouncementsSuccessAction,
  GetEventsAction,
  GetEventsFailedAction,
  GetEventsSuccessAction,
  GetMoreEventsAction,
  GetMoreEventsFailedAction,
  GetMoreEventsSuccessAction,
} from './events.actions';

const ApiCalls = {
  GET_ANNOUNCEMENTS: 'solutions.events.announcements',
  GET_EVENTS: 'solutions.events.load',
  ADD_TO_CALENDAR: 'solutions.events.addtocalender',
};

@Injectable()
export class EventsEffects {
  @Effect() getAnnouncements$ = this.actions$.pipe(
    ofType<GetAnnouncementsAction>(EventsActionTypes.GET_ANNOUNCEMENTS),
    switchMap(() => this.rogerthatService.apiCall<EventAnnouncementList>(ApiCalls.GET_ANNOUNCEMENTS).pipe(
      map(result => new GetAnnouncementsSuccessAction(result)),
      catchError(err => of(new GetAnnouncementsFailedAction(err)))),
    ));
  @Effect() getEvents$ = this.actions$.pipe(
    ofType<GetEventsAction>(EventsActionTypes.GET_EVENTS),
    switchMap(action => this.rogerthatService.apiCall<OcaEventList>(ApiCalls.GET_EVENTS, action.payload).pipe(
      map(result => new GetEventsSuccessAction(result)),
      catchError(err => {
        this.errorService.showErrorDialog(action, err);
        return of(new GetEventsFailedAction(err));
      })),
    ));

  @Effect() getMoreEvents$ = this.actions$.pipe(
    ofType<GetMoreEventsAction>(EventsActionTypes.GET_MORE_EVENTS),
    switchMap(action => this.rogerthatService.apiCall<OcaEventList>(ApiCalls.GET_EVENTS, action.payload).pipe(
      map(result => new GetMoreEventsSuccessAction(result)),
      catchError(err => {
        this.errorService.showErrorDialog(action, err);
        return of(new GetMoreEventsFailedAction(err));
      })),
    ));

  @Effect() addToCalendar = this.actions$.pipe(
    ofType<AddEventToCalendarAction>(EventsActionTypes.ADD_EVENT_TO_CALENDAR),
    switchMap(action => {
        return this.rogerthatService.apiCall<{ message: string }>(ApiCalls.ADD_TO_CALENDAR, action.payload).pipe(
          map(result => new AddEventToCalendarSuccessAction(result)),
          tap(async result => {
            const dialog = await this.alertController.create({
              message: result.payload.message,
              buttons: [{ text: this.translate.instant('app.oca.close') }],
            });
            await dialog.present();
          }),
          catchError(err => {
            this.errorService.showErrorDialog(action, err);
            return of(new AddEventToCalendarFailedAction(err));
          }));
      },
    ));

  constructor(private actions$: Actions<EventsActions>,
              private store: Store<AppState>,
              private alertController: AlertController,
              private translate: TranslateService,
              private errorService: ErrorService,
              private router: Router,
              private rogerthatService: RogerthatService) {
  }
}
