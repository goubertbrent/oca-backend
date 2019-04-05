import { ChangeDetectionStrategy, Component, OnDestroy, OnInit, ViewEncapsulation } from '@angular/core';
import { MatDialog } from '@angular/material';
import { ActivatedRoute } from '@angular/router';
import { Actions, ofType } from '@ngrx/effects';
import { select, Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { Observable, Subject, Subscription } from 'rxjs';
import { tap } from 'rxjs/internal/operators/tap';
import { withLatestFrom } from 'rxjs/internal/operators/withLatestFrom';
import { first, take, takeUntil } from 'rxjs/operators';
import { SimpleDialogComponent, SimpleDialogData } from '../../../shared/dialog/simple-dialog.component';
import { Loadable } from '../../../shared/loadable/loadable';
import {
  UserAutoCompleteDialogComponent,
  UserDialogData,
} from '../../../shared/users/components/user-auto-complete-dialog/user-auto-complete-dialog.component';
import { UserDetailsTO } from '../../../shared/users/interfaces';
import { createAppUser } from '../../../shared/util/rogerthat';
import { FormDetailTab } from '../../components/form-detail/form-detail.component';
import {
  CopyFormAction,
  DeleteAllResponsesAction,
  DeleteResponseAction,
  FormsActions,
  FormsActionTypes,
  GetFormAction,
  GetFormStatisticsAction,
  GetNextResponseAction,
  GetResponsesAction,
  GetTombolaWinnersAction,
  SaveFormAction,
  ShowDeleteAllResponsesAction,
  TestFormAction,
} from '../../forms.actions';
import { FormsState, getForm, getFormResponse, getResponsesData, getTombolaWinners, getTransformedStatistics } from '../../forms.state';
import { OptionsMenuOption } from '../../interfaces/consts';
import { OptionType } from '../../interfaces/enums';
import { FormStatisticsView, OcaForm, SaveForm, SingleFormResponse } from '../../interfaces/forms.interfaces';

@Component({
  selector: 'oca-form-details-page',
  templateUrl: './form-details-page.component.html',
  encapsulation: ViewEncapsulation.None,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class FormDetailsPageComponent implements OnInit, OnDestroy {
  form$: Observable<Loadable<OcaForm>>;
  formStatistics$: Observable<Loadable<FormStatisticsView>>;
  tombolaWinners$: Observable<UserDetailsTO[]>;
  formResponse$: Observable<Loadable<SingleFormResponse>>;
  formId: number;
  wasVisible: null | boolean = null;

  private _subscription: Subscription = Subscription.EMPTY;
  private _destroyed = new Subject();

  constructor(private store: Store<FormsState>,
              private actions$: Actions<FormsActions>,
              private route: ActivatedRoute,
              private matDialog: MatDialog,
              private translate: TranslateService) {
  }

  ngOnInit() {
    this.formId = this.route.snapshot.params.id;
    this.store.dispatch(new GetFormAction(this.formId));
    this.form$ = this.store.pipe(select(getForm), tap(form => {
      if (form.success && this.wasVisible === null && form.data) {
        this.wasVisible = form.data.settings.visible;
      }
    }));
    this.tombolaWinners$ = this.store.pipe(select(getTombolaWinners));
    this.formStatistics$ = this.store.pipe(select(getTransformedStatistics));
    this.formResponse$ = this.store.pipe(select(getFormResponse));
  }

  ngOnDestroy(): void {
    this._subscription.unsubscribe();
    this._destroyed.next();
    this._destroyed.complete();
  }

  onSave(event: SaveForm) {
    if (!this.wasVisible && event.data.settings.visible) {
      // Changed from invisible to visible - ask to delete responses
      this.store.dispatch(new GetFormStatisticsAction(this.formId));
      this.actions$.pipe(ofType(FormsActionTypes.GET_FORM_STATISTICS_COMPLETE), take(1)).subscribe(result => {
        if (result.stats.submissions === 0) {
          this.store.dispatch(new SaveFormAction(event));
        } else {
          this.matDialog.open(SimpleDialogComponent, {
            data: {
              ok: this.translate.instant('oca.yes'),
              message: this.translate.instant('oca.responses_found_for_form', { responseCount: result.stats.submissions }),
              title: this.translate.instant('oca.confirm_deletion'),
              cancel: this.translate.instant('oca.no'),
            } as SimpleDialogData,
          }).afterClosed().subscribe(dialogResult => {
            if (dialogResult.submitted) {
              this.store.dispatch(new DeleteAllResponsesAction(this.formId));
            }
            this.store.dispatch(new SaveFormAction(event));
          });
        }
      });
    } else {
      this.store.dispatch(new SaveFormAction(event));
    }
    this.wasVisible = event.data.settings.visible;
  }

  onTabChanged(tabIndex: number) {
    switch (tabIndex) {
      case FormDetailTab.TOMBOLA_WINNERS:
        this.store.dispatch(new GetTombolaWinnersAction(this.formId));
        break;
      case FormDetailTab.RESPONSES:
        this.store.pipe(select(getResponsesData), take(1)).subscribe(data => {
          if (data.more && !data.ids.length) {
            this.store.dispatch(new GetResponsesAction({ formId: this.formId, page_size: 5 }));
          }
        });
        break;
      case FormDetailTab.STATISTICS:
        this.store.dispatch(new GetFormStatisticsAction(this.formId));
        break;
    }
  }

  onMenuOptionClicked(option: OptionsMenuOption) {
    if (option.id === OptionType.DELETE_ALL_RESPONSES) {
      this.form$.pipe(first()).subscribe(form => {
        this.store.dispatch(new ShowDeleteAllResponsesAction(this.formId, this.translate.instant('oca.confirm_delete_responses')));
      });
    }
  }

  testForm() {
    // TODO: if user hasn't saved yet, ask to save first
    const data: UserDialogData = {
      cancel: this.translate.instant('oca.cancel'),
      message: this.translate.instant('oca.enter_email_used_in_app'),
      title: this.translate.instant('oca.test_form'),
      ok: this.translate.instant('oca.send_form'),
    };
    this._subscription.unsubscribe();
    this._subscription = this.matDialog.open(UserAutoCompleteDialogComponent, { data }).afterClosed().pipe(
      withLatestFrom(this.form$),
      take(1),
    ).subscribe(([ result, formData ]: [ UserDetailsTO | null, Loadable<OcaForm> ]) => {
      if (result && formData.data) {
        this.store.dispatch(new TestFormAction(formData.data.form.id, [ createAppUser(result.email, result.app_id) ]));
      }
    });
  }

  copyForm() {
    this.store.dispatch(new CopyFormAction(this.formId));
  }

  createNews() {
    this.form$.pipe(take(1), takeUntil(this._destroyed)).subscribe(form => {
      if (!form.data) {
        return;
      }
      const message = form.data.form.sections[ 0 ].description || form.data.form.sections[ 0 ].components[ 0 ].description;
      const buttonValue = JSON.stringify({ '__rt__.tag': '__sln__.forms', id: form.data.form.id });
      const data = {
        type: 'oca.news.create_news',
        data: {
          app_ids: [],
          broadcast_on_facebook: false,
          broadcast_on_twitter: false,
          buttons: [ {
            action: `smi://${buttonValue}`,
            caption: form.data.form.title,
            flow_params: '{}',
            id: buttonValue,
          } ],
          feed_names: [],
          media: null,
          message,
          published: false,
          qr_code_caption: null,
          qr_code_content: null,
          role_ids: [],
          scheduled_at: 0,
          sticky: false,
          sticky_until: 0,
          tags: [ 'news' ],
          target_audience: null,
          title: form.data.form.title,
          type: 1,
        },
      };
      window.top.postMessage(data, '*');
    });
  }

  onTestForm(user?: UserDetailsTO) {
    if (!user) {
      return;
    }
    const userEmail = createAppUser(user.email, user.app_id);
    this.form$.pipe(
      take(1),
      takeUntil(this._destroyed),
    ).subscribe(result => {
      if (result && result.data) {
        this.store.dispatch(new TestFormAction(result.data.form.id, [ userEmail ]));
      }
    });
  }

  onNextResponse(responseId: number | null) {
    this.store.dispatch(new GetNextResponseAction({ formId: this.formId, responseId }));
  }

  onRemoveResponse(data: {formId: number, submissionId: number}) {
    this.store.dispatch(new DeleteResponseAction(data));
  }
}
