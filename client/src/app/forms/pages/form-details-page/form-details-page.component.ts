import { ChangeDetectionStrategy, Component, OnDestroy, OnInit, ViewEncapsulation } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { ActivatedRoute, Router } from '@angular/router';
import { Actions, ofType } from '@ngrx/effects';
import { select, Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { Observable, Subject, Subscription } from 'rxjs';
import { first, map, take, takeUntil, tap, withLatestFrom } from 'rxjs/operators';
import { CreateNews } from '../../../news/interfaces';
import { SimpleDialogComponent, SimpleDialogData } from '../../../shared/dialog/simple-dialog.component';
import { NewsGroupType } from '../../../shared/interfaces/rogerthat';
import { Loadable } from '../../../shared/loadable/loadable';
import {
  UserAutoCompleteDialogComponent,
  UserDialogData,
} from '../../../shared/users/components/user-auto-complete-dialog/user-auto-complete-dialog.component';
import { UserDetailsTO } from '../../../shared/users/users';
import { deepCopy } from '../../../shared/util/misc';
import { createAppUser } from '../../../shared/util/rogerthat';
import { FormDetailTab } from '../../components/form-detail/form-detail.component';
import { ImportFormDialogComponent } from '../../components/import-form-dialog/import-form-dialog.component';
import {
  CopyFormAction,
  DeleteAllResponsesAction,
  DeleteResponseAction,
  DownloadResponsesAction,
  FormsActions,
  FormsActionTypes,
  GetFormAction,
  GetFormStatisticsAction,
  GetNextResponseAction,
  GetResponsesAction,
  GetTombolaWinnersAction,
  ImportFormAction,
  SaveFormAction,
  ShowDeleteAllResponsesAction,
  TestFormAction,
} from '../../forms.actions';
import {
  FormsState,
  getActiveIntegrations,
  getForm,
  getFormResponse,
  getTombolaWinners,
  getTransformedStatistics,
} from '../../forms.state';
import { OptionsMenuOption } from '../../interfaces/consts';
import { OptionType } from '../../interfaces/enums';
import { CreateDynamicForm, FormStatisticsView, OcaForm, SaveForm, SingleFormResponse } from '../../interfaces/forms';
import { FormIntegrationConfiguration } from '../../interfaces/integrations';

@Component({
  selector: 'oca-form-details-page',
  templateUrl: './form-details-page.component.html',
  encapsulation: ViewEncapsulation.None,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class FormDetailsPageComponent implements OnInit, OnDestroy {
  form$: Observable<Loadable<OcaForm>>;
  formStatistics$: Observable<Loadable<FormStatisticsView | null>>;
  tombolaWinners$: Observable<UserDetailsTO[]>;
  formResponse$: Observable<Loadable<SingleFormResponse>>;
  activeIntegrations$: Observable<FormIntegrationConfiguration[]>;
  formId: number;
  wasVisible: null | boolean = null;

  private _subscription: Subscription = Subscription.EMPTY;
  private _destroyed = new Subject();

  constructor(private store: Store<FormsState>,
              private actions$: Actions<FormsActions>,
              private route: ActivatedRoute,
              private matDialog: MatDialog,
              private translate: TranslateService,
              private router: Router) {
  }

  ngOnInit() {
    this.formId = this.route.snapshot.params.id;
    this.store.dispatch(new GetFormAction(this.formId));
    this.form$ = this.store.pipe(select(getForm), map(f => deepCopy(f)), tap(form => {
      if (form.success && this.wasVisible === null && form.data) {
        this.wasVisible = form.data.settings.visible;
      }
    }));
    this.tombolaWinners$ = this.store.pipe(select(getTombolaWinners));
    this.formStatistics$ = this.store.pipe(select(getTransformedStatistics));
    this.formResponse$ = this.store.pipe(select(getFormResponse));
    this.activeIntegrations$ = this.store.pipe(select(getActiveIntegrations));
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
              ok: this.translate.instant('oca.Yes'),
              message: this.translate.instant('oca.responses_found_for_form', { responseCount: result.stats.submissions }),
              title: this.translate.instant('oca.confirm_deletion'),
              cancel: this.translate.instant('oca.No'),
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
        this.store.dispatch(new GetResponsesAction({ formId: this.formId, page_size: 5 }, true));
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
      cancel: this.translate.instant('oca.Cancel'),
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

  downloadResponses() {
    this.store.dispatch(new DownloadResponsesAction({ id: this.formId }));
  }

  createNews() {
    this.form$.pipe(take(1), takeUntil(this._destroyed)).subscribe(form => {
      if (!form.data) {
        return;
      }
      const message = form.data.form.sections[ 0 ].description || form.data.form.sections[ 0 ].components[ 0 ].description || '';
      const buttonValue = JSON.stringify({ '__rt__.tag': '__sln__.forms', id: form.data.form.id });
      const data: Partial<CreateNews> = {
        action_button: {
          action: `smi://${buttonValue}`,
          caption: form.data.form.title.substring(0, 15),
          flow_params: '{}',
          id: buttonValue,
        },
        message,
        title: form.data.form.title,
        type: 1,
        group_type: form.data.settings.visible_until ? NewsGroupType.POLLS : NewsGroupType.CITY,
        group_visible_until: form.data.settings.visible_until ? new Date(form.data.settings.visible_until) : null,
      };
      localStorage.setItem('news.item', JSON.stringify(data));
      this.router.navigate(['news', 'create']);
      window.top.postMessage({ type: 'oca.set_navigation', path: 'news' }, '*');
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

  onRemoveResponse(data: { formId: number, submissionId: number }) {
    this.store.dispatch(new DeleteResponseAction(data));
  }

  showDeveloperInfo() {
    this.form$.pipe(
      take(1),
      takeUntil(this._destroyed),
    ).subscribe(result => {
      if (result?.data) {
        const message = `${this.translate.instant('oca.form_id')} <pre>${result.data.form.id}</pre>
${this.translate.instant('oca.version')} <pre>${result.data.form.version}</pre>`;
        this.matDialog.open(SimpleDialogComponent, {
          data: {
            ok: this.translate.instant('oca.Close'),
            message,
            title: this.translate.instant('oca.developer_information'),
          } as SimpleDialogData,
        });
      }
    });
  }

  exportForm() {
    this.form$.pipe(
      take(1),
      takeUntil(this._destroyed),
    ).subscribe(result => {
      // tslint:disable-next-line:no-non-null-assertion
      const form = result.data!.form;
      const exportedForm: Partial<CreateDynamicForm> = {
        sections: form.sections,
        max_submissions: form.max_submissions,
        submission_section: form.submission_section,
      };
      const blob = new Blob([JSON.stringify({ version: 1, form: exportedForm })], { type: 'application/json;charset=utf-8' });
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = `${form.title}.json`;
      a.rel = 'noopener';
      a.dispatchEvent(new MouseEvent('click'));
      setTimeout(() => URL.revokeObjectURL(a.href), 1e4); // revoke url after 10 seconds
    });
  }

  importForm() {
    this.matDialog.open(ImportFormDialogComponent).afterClosed().subscribe((result: Partial<CreateDynamicForm>) => {
      this.store.dispatch(new ImportFormAction({form: result}));
    });
  }
}
