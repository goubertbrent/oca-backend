import { ChangeDetectionStrategy, Component, OnDestroy, OnInit, ViewEncapsulation } from '@angular/core';
import { MatDialog } from '@angular/material';
import { ActivatedRoute } from '@angular/router';
import { Actions, ofType } from '@ngrx/effects';
import { select, Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { Observable, Subscription } from 'rxjs';
import { tap } from 'rxjs/internal/operators/tap';
import { first, map, take, withLatestFrom } from 'rxjs/operators';
import { SimpleDialogComponent, SimpleDialogData } from '../../../dialog/simple-dialog.component';
import { OptionsMenuOption } from '../../../interfaces/consts';
import { OptionType } from '../../../interfaces/enums';
import { FormStatisticsView, OcaForm } from '../../../interfaces/forms.interfaces';
import { Loadable } from '../../../interfaces/loadable';
import {
  UserAutoCompleteDialogComponent,
  UserDialogData,
} from '../../../users/components/user-auto-complete-dialog/user-auto-complete-dialog.component';
import { UserDetailsTO } from '../../../users/interfaces';
import { createAppUser } from '../../../util/rogerthat';
import { FormDetailTab } from '../../components/form-detail/form-detail.component';
import {
  DeleteAllResponsesAction,
  FormsActions,
  FormsActionTypes,
  GetFormAction,
  GetFormStatisticsAction,
  GetTombolaWinnersAction,
  SaveFormAction,
  ShowDeleteAllResponsesAction,
  TestFormAction,
} from '../../forms.actions';
import { FormsState, getForm, getTombolaWinners, getTransformedStatistics } from '../../forms.state';

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
  showCreateNewsButton$: Observable<boolean>;
  formId: number;
  wasVisible: null | boolean = null;

  private _subscription: Subscription = Subscription.EMPTY;

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
      if (form.success && this.wasVisible === null) {
        this.wasVisible = form.data.settings.visible;
      }
    }));
    this.tombolaWinners$ = this.store.pipe(select(getTombolaWinners));
    this.formStatistics$ = this.store.pipe(select(getTransformedStatistics));
    this.showCreateNewsButton$ = this.form$.pipe(map(loadable => loadable.success && loadable.data.settings.visible));
  }

  ngOnDestroy(): void {
    this._subscription.unsubscribe();
  }

  onSave(form: OcaForm) {
    if (!this.wasVisible && form.settings.visible) {
      // Changed from invisible to visible - ask to delete responses
      this.store.dispatch(new GetFormStatisticsAction(this.formId));
      this.actions$.pipe(ofType(FormsActionTypes.GET_FORM_STATISTICS_COMPLETE), take(1)).subscribe(result => {
        if (result.stats.submissions === 0) {
          this.store.dispatch(new SaveFormAction(form));
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
            this.store.dispatch(new SaveFormAction(form));
          });
        }
      });
    } else {
      this.store.dispatch(new SaveFormAction(form));
    }
    this.wasVisible = form.settings.visible;
  }

  onTabChanged(tabIndex: number) {
    switch (tabIndex) {
      case FormDetailTab.TOMBOLA_WINNERS:
        this.form$.pipe(first()).subscribe(form => {
          this.store.dispatch(new GetTombolaWinnersAction(form.data.settings.id));
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
      first(),
    ).subscribe(([ result, formData ]: [ UserDetailsTO | null, Loadable<OcaForm> ]) => {
      if (result) {
        this.store.dispatch(new TestFormAction(formData.data.form.id, [ createAppUser(result.email, result.app_id) ]));
      }
    });
  }

  createNews() {
    // TODO: if user hasn't saved yet, ask to save first
    this.form$.pipe(first()).subscribe(form => {
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


}
