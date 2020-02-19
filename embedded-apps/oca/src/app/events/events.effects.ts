import { Injectable } from '@angular/core';
import { Router } from '@angular/router';
import { AlertController } from '@ionic/angular';
import { Actions, Effect, ofType } from '@ngrx/effects';
import { Action, Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { of } from 'rxjs';
import { catchError, map, switchMap, tap } from 'rxjs/operators';
import { AppState } from '../reducers';
import { RogerthatService } from '../rogerthat';
import { OcaEventList } from './events';
import {
  AddEventToCalendarAction,
  AddEventToCalendarFailedAction,
  AddEventToCalendarSuccessAction,
  EventsActions,
  EventsActionTypes,
  GetEventsAction,
  GetEventsFailedAction,
  GetEventsSuccessAction,
  GetMoreEventsAction,
  GetMoreEventsFailedAction,
  GetMoreEventsSuccessAction,
} from './events.actions';

const ApiCalls = {
  GET_EVENTS: 'solutions.events.load',
  ADD_TO_CALENDAR: 'solutions.events.addtocalender',
};

@Injectable()
export class EventsEffects {
  @Effect() getEvents$ = this.actions$.pipe(
    ofType<GetEventsAction>(EventsActionTypes.GET_EVENTS),
    switchMap(action => this.rogerthatService.apiCall<OcaEventList>(ApiCalls.GET_EVENTS, action.payload).pipe(
      map(result => new GetEventsSuccessAction(result)),
      catchError(err => {
        this.showErrorDialog(action, err);
        return of(new GetEventsFailedAction(err));
      })),
    ));

  @Effect() getMoreEvents$ = this.actions$.pipe(
    ofType<GetMoreEventsAction>(EventsActionTypes.GET_MORE_EVENTS),
    switchMap(action => this.rogerthatService.apiCall<OcaEventList>(ApiCalls.GET_EVENTS, action.payload).pipe(
      map(result => new GetMoreEventsSuccessAction(result)),
      catchError(err => {
        this.showErrorDialog(action, err);
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
            this.showErrorDialog(action, err);
            return of(new AddEventToCalendarFailedAction(err));
          }));
      },
    ));

  constructor(private actions$: Actions<EventsActions>,
              private store: Store<AppState>,
              private alertController: AlertController,
              private translate: TranslateService,
              private router: Router,
              private rogerthatService: RogerthatService) {
  }

  // todo use errorService for this when jcc is merged
  private async showErrorDialog<T extends Action>(failedAction: T, error: any) {
    let errorMessage: string;
    if (typeof error === 'string') {
      errorMessage = error;
    } else {
      errorMessage = this.translate.instant('app.oca.unknown_error');
    }
    const top = await this.alertController.getTop();
    if (top) {
      await top.dismiss();
    }
    const dialog = await this.alertController.create({
      header: this.translate.instant('app.oca.error'),
      message: errorMessage,
      buttons: [
        {
          text: this.translate.instant('app.oca.close'),
          role: 'cancel',
        },
        {
          text: this.translate.instant('app.oca.retry'),
          handler: () => {
            this.store.dispatch(failedAction);
          },
        },
      ],
    });
    await dialog.present();
  }
}
