import { ChangeDetectionStrategy, Component, OnDestroy, OnInit, ViewEncapsulation } from '@angular/core';
import { MatDialog } from '@angular/material';
import { ActivatedRoute } from '@angular/router';
import { select, Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { Observable, Subscription } from 'rxjs';
import { first, map, withLatestFrom } from 'rxjs/operators';
import { FormDetailTab } from '../form-detail/form-detail.component';
import { GetFormAction, GetFormStatisticsAction, GetTombolaWinnersAction, SaveFormAction, TestFormAction } from '../forms/forms.actions';
import { FormsState, getForm, getFormStatistics, getTombolaWinners } from '../forms/forms.state';
import { FormStatistics, OcaForm } from '../interfaces/forms.interfaces';
import { Loadable } from '../interfaces/loadable';
import {
  UserAutoCompleteDialogComponent,
  UserDialogData,
} from '../users/components/user-auto-complete-dialog/user-auto-complete-dialog.component';
import { UserDetailsTO } from '../users/interfaces';

@Component({
  selector: 'oca-form-details-page',
  templateUrl: './form-details-page.component.html',
  encapsulation: ViewEncapsulation.None,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class FormDetailsPageComponent implements OnInit, OnDestroy {
  form$: Observable<Loadable<OcaForm>>;
  formStatistics$: Observable<Loadable<FormStatistics>>;
  tombolaWinners$: Observable<UserDetailsTO[]>;
  showCreateNewsButton$: Observable<boolean>;

  private _subscription: Subscription = Subscription.EMPTY;

  constructor(private store: Store<FormsState>,
              private route: ActivatedRoute,
              private matDialog: MatDialog,
              private translate: TranslateService) {
  }

  ngOnInit() {
    this.store.dispatch(new GetFormAction(this.route.snapshot.params.id));
    this.form$ = this.store.pipe(select(getForm));
    this.tombolaWinners$ = this.store.pipe(select(getTombolaWinners));
    this.formStatistics$ = this.store.pipe(select(getFormStatistics));
    this.showCreateNewsButton$ = this.form$.pipe(map(loadable => loadable.success && loadable.data.settings.visible));
  }

  ngOnDestroy(): void {
    this._subscription.unsubscribe();
  }

  onSave(form: OcaForm) {
    this.store.dispatch(new SaveFormAction(form));
  }

  onTabChanged(tabIndex: number) {
    switch (tabIndex) {
      case FormDetailTab.TOMBOLA:
        this.form$.pipe(first()).subscribe(form => {
          if (form.data && form.data && form.data.settings.finished) {
            this.store.dispatch(new GetTombolaWinnersAction(form.data.settings.id));
          }
        });
        break;
      case FormDetailTab.STATISTICS:
        this.store.dispatch(new GetFormStatisticsAction(this.route.snapshot.params.id));
        break;
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
        this.store.dispatch(new TestFormAction(formData.data.form.id, [ result.email ]));
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
