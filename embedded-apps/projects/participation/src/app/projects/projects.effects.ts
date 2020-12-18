import { DatePipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { AlertController, LoadingController, ToastController } from '@ionic/angular';
import { AlertOptions, LoadingOptions } from '@ionic/core';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { select, Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { of } from 'rxjs';
import { catchError, map, switchMap, tap, withLatestFrom } from 'rxjs/operators';
import { ErrorService } from '../error.service';
import { createAppUser, filterNull } from '../util';
import {
  AddParticipationAction,
  AddParticipationCompleteAction,
  AddParticipationFailedAction,
  GetCityAction,
  GetCityCompleteAction,
  GetCityFailedAction,
  GetMerchantAction,
  GetMerchantCompleteAction,
  GetMerchantFailedAction,
  GetMerchantsAction,
  GetMerchantsCompleteAction,
  GetMerchantsFailedAction,
  GetMoreMerchantsAction,
  GetMoreMerchantsCompleteAction,
  GetMoreMerchantsFailedAction,
  GetProjectDetailsAction,
  GetProjectDetailsCompleteAction,
  GetProjectDetailsFailedAction,
  GetProjectsAction,
  GetProjectsCompleteAction,
  GetProjectsFailedAction,
  GetUserSettingsAction,
  GetUserSettingsCompleteAction,
  GetUserSettingsFailedAction,
  ProjectsActions,
  ProjectsActionTypes,
  SaveUserSettingsAction,
  SaveUserSettingsCompleteAction,
  SaveUserSettingsFailedAction,
} from './projects.actions';
import { ProjectsService } from './projects.service';
import { getCurrentProject, getMerchants, ProjectsState } from './projects.state';

@Injectable()
export class ProjectsEffects {

   getCity$ = createEffect(() => this.actions$.pipe(
    ofType<GetCityAction>(ProjectsActionTypes.GET_CITY),
    switchMap(() => this.projectsService.getCity(rogerthat.user.communityId).pipe(
      map(data => new GetCityCompleteAction(data)),
      catchError(err => of(new GetCityFailedAction(err)))),
    )));

   getProjects$ = createEffect(() => this.actions$.pipe(
    ofType<GetProjectsAction>(ProjectsActionTypes.GET_PROJECTS),
    switchMap(() => this.projectsService.getProjects(rogerthat.user.communityId).pipe(
      map(data => new GetProjectsCompleteAction(data)),
      catchError(err => of(new GetProjectsFailedAction(err)))),
    )));

   getProjectDetails$ = createEffect(() => this.actions$.pipe(
    ofType<GetProjectDetailsAction>(ProjectsActionTypes.GET_PROJECT_DETAILS),
    switchMap(action => this.projectsService.getProjectDetails(rogerthat.user.communityId, action.payload.id,
      createAppUser(rogerthat.user.account, rogerthat.system.appId)).pipe(
      map(data => new GetProjectDetailsCompleteAction(data)),
      catchError(err => of(new GetProjectDetailsFailedAction(err)))),
    )));

   addParticipation$ = createEffect(() => this.actions$.pipe(
    ofType<AddParticipationAction>(ProjectsActionTypes.ADD_PARTICIPATION),
    tap(() => this.showDialog({
      type: 'loading',
      options: {
        message: this.translate.instant('loading'),
        translucent: true,
        backdropDismiss: true,
      },
    })),
    switchMap(action => {
        return this.projectsService.addParticipation({
          project_id: action.payload.projectId,
          qr_content: action.payload.qrContent,
          app_id: rogerthat.system.appId,
          email: rogerthat.user.account,
        }).pipe(
          map(data => new AddParticipationCompleteAction(data)),
          tap(() => {
            this.dismissDialog('loading');
            this.toastController.create({
              message: this.translate.instant('scan_added'),
              duration: 5000,
              buttons: [{ text: this.translate.instant('ok') }],
            }).then(toast => toast.present()).catch(e => console.error(e));
          }),
          catchError(err => {
            const errorMsg = this.getErrorMessage(err);
            this.dismissDialog('loading');
            this.showDialog({
              type: 'alert',
              options: {
                ...errorMsg,
                buttons: [this.translate.instant('ok')],
              },
            });
            return of(new AddParticipationFailedAction(errorMsg.message));
          }));
      },
    )));

   getMerchant$ = createEffect(() => this.actions$.pipe(
    ofType<GetMerchantAction>(ProjectsActionTypes.GET_MERCHANT),
    withLatestFrom(this.store.pipe(select(getMerchants))),
    switchMap(([action, merchants]) => {
        if (merchants) {
          const merchant = merchants.results.find(m => m.id === action.payload.id);
          if (merchant) {
            return of(new GetMerchantCompleteAction(merchant));
          }
        }
        return this.projectsService.getMerchant(rogerthat.user.communityId, action.payload.id).pipe(
          map(data => new GetMerchantCompleteAction(data)),
          catchError(err => of(new GetMerchantFailedAction(this.getErrorMessage(err).message))));
      },
    )));

   getCityMerchants$ = createEffect(() => this.actions$.pipe(
    ofType<GetMerchantsAction>(ProjectsActionTypes.GET_MERCHANTS),
    switchMap(() => this.projectsService.getCityMerchants(rogerthat.user.communityId).pipe(
      map(data => new GetMerchantsCompleteAction(data)),
      catchError(err => of(new GetMerchantsFailedAction(this.getErrorMessage(err).message)))),
    )));

   getMoreProjectMerchants$ = createEffect(() => this.actions$.pipe(
    ofType<GetMoreMerchantsAction>(ProjectsActionTypes.GET_MORE_MERCHANTS),
    switchMap(action => this.store.pipe(
      select(getCurrentProject),
      map(p => p.result),
      filterNull(),
      withLatestFrom(this.store.pipe(select(getMerchants))),
      map(([project, list]) => this.projectsService.getCityMerchants(project.city_id, list?.cursor).pipe(
        map(data => new GetMoreMerchantsCompleteAction(data)),
        catchError(err => of(new GetMoreMerchantsFailedAction(this.getErrorMessage(err).message)))),
      )))));

   getUserSettings$ = createEffect(() => this.actions$.pipe(
    ofType<GetUserSettingsAction>(ProjectsActionTypes.GET_USER_SETTINGS),
    switchMap(() => this.projectsService.getUserSettings(createAppUser(rogerthat.user.account, rogerthat.system.appId)).pipe(
      map(data => new GetUserSettingsCompleteAction(data)),
      catchError(err => of(new GetUserSettingsFailedAction(this.getErrorMessage(err).message)))),
    )));
   saveUserSettings$ = createEffect(() => this.actions$.pipe(
    ofType<SaveUserSettingsAction>(ProjectsActionTypes.SAVE_USER_SETTINGS),
    switchMap(a => this.projectsService.saveUserSettings(createAppUser(rogerthat.user.account, rogerthat.system.appId), a.payload).pipe(
      map(data => new SaveUserSettingsCompleteAction(data)),
      catchError(err => of(new SaveUserSettingsFailedAction(this.getErrorMessage(err).message)))),
    )));

  constructor(private actions$: Actions<ProjectsActions>,
              private store: Store<ProjectsState>,
              private projectsService: ProjectsService,
              private translate: TranslateService,
              private datePipe: DatePipe,
              private alertController: AlertController,
              private loadingController: LoadingController,
              private errorService: ErrorService,
              private toastController: ToastController) {
  }

  private async dismissDialog(dialogType: 'loading') {
    try {
      dialogType === 'loading' ? await this.loadingController.dismiss() : await this.alertController.dismiss();
    } catch (ignored) {
    }
  }

  private async showDialog(data: { type: 'loading', options: LoadingOptions } | { type: 'alert', options: AlertOptions }) {
    let dialog: HTMLIonLoadingElement | HTMLIonAlertElement;
    if (data.type === 'loading') {
      dialog = await this.loadingController.create(data.options);
    } else {
      dialog = await this.alertController.create(data.options);
    }
    // arbitrary delay to allow creating / hiding other dialogs that might have been shown just before
    setTimeout(async () => {
      try {
        await this.loadingController.dismiss();
        await this.alertController.dismiss();
      } catch (ignored) {
        // Throws error in case there was no dialog, but we don't actually care
      }
      await dialog.present();
    }, 50);
  }

  private getErrorMessage(response: HttpErrorResponse): { header: string, message: string } {
    const result = {
      header: this.translate.instant('error'),
      message: '',
    };
    if (response.status.toString().startsWith('4') && response.error && response.error.error) {
      if (response.error.error === 'psp.errors.already_scanned_recently') {
        const now = new Date();
        const scanDate = new Date(response.error.data.date);
        const diffTime = Math.abs(now.getTime() - scanDate.getTime());
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        const format = diffDays > 1 ? 'medium' : 'shortTime';
        const date = this.datePipe.transform(response.error.data.date, format);
        result.message = this.translate.instant(response.error.error, { date });
        result.header = this.translate.instant('info');
      } else {
        result.message = this.translate.instant(response.error.error, response.error.data);
      }
    } else {
      result.message = this.translate.instant('unknown_error');
    }
    return result;
  }
}
