import { ChangeDetectionStrategy, Component, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { NgForm } from '@angular/forms';
import { MatSlideToggleChange } from '@angular/material/slide-toggle';
import { ActivatedRoute, Router } from '@angular/router';
import { Actions, ofType } from '@ngrx/effects';
import { Store } from '@ngrx/store';
import { Observable, Subscription } from 'rxjs';
import { map } from 'rxjs/operators';
import { ApiRequestStatus } from '../../../../framework/client/rpc';
import {
  AppsActionTypes,
  ClearAppAction,
  CreateAppAction,
  CreateAppCompleteAction,
  GetContactsAction,
  GetDeveloperAccountsAction,
  GetReviewNotesListAction,
} from '../../actions';
import * as states from '../../console.state';
import { getReviewNotesList } from '../../console.state';
import {
  APP_TYPES,
  AppTypes,
  Contact,
  COUNTRIES,
  CreateAppPayload,
  DeveloperAccount,
  LANGUAGES,
  NEWS_STREAM_TYPES,
  NewsStreamTypes,
  ReviewNotes,
} from '../../interfaces';

@Component({
  selector: 'rcc-app-create',
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: 'create-app.component.html',
})
export class CreateAppComponent implements OnInit, OnDestroy {
  @ViewChild('form', { static: true }) form: NgForm;
  app: CreateAppPayload;
  androidDeveloperAccounts$: Observable<DeveloperAccount[]>;
  iosDeveloperAccounts$: Observable<DeveloperAccount[]>;
  createAppStatus$: Observable<ApiRequestStatus>;
  contacts$: Observable<Contact[]>;
  reviewNotes$: Observable<ReviewNotes[]>;
  appTypes = APP_TYPES;
  newsStreamTypes = NEWS_STREAM_TYPES;
  languages = LANGUAGES;
  countries = COUNTRIES;

  private _createAppSubscription: Subscription;

  constructor(private store: Store,
              private actions$: Actions,
              private router: Router,
              private route: ActivatedRoute) {
  }

  ngOnInit() {
    this.contacts$ = this.store.select(states.getContacts);
    this.createAppStatus$ = this.store.select(states.createAppStatus);
    this.androidDeveloperAccounts$ = this.store.select(states.getDeveloperAccounts)
      .pipe(map(accs => accs.filter(a => a.type === 'android')));
    this.iosDeveloperAccounts$ = this.store.select(states.getDeveloperAccounts)
      .pipe(map(accs => accs.filter(a => a.type === 'ios')));
    this.reviewNotes$ = this.store.select(getReviewNotesList);
    this.store.dispatch(new GetDeveloperAccountsAction());
    this.store.dispatch(new GetContactsAction());
    this.store.dispatch(new GetReviewNotesListAction());
    this.store.dispatch(new ClearAppAction());
    this.app = {
      app_type: AppTypes.CITY_APP,
      title: '',
      main_language: 'nl',
      app_id: '',
      auto_added_services: [],
      country: 'BE',
      official_id: null,
      contact: null,
      dashboard_email_address: '',
      ios_developer_account: null,
      android_developer_account: null,
      review_notes: null,
      news_stream: null,
    };
    this._createAppSubscription = this.actions$.pipe(ofType<CreateAppCompleteAction>(AppsActionTypes.CREATE_APP_COMPLETE))
      .subscribe(action => this.router.navigate(['..', action.payload.app_id], { relativeTo: this.route }));
  }

  ngOnDestroy() {
    this._createAppSubscription.unsubscribe();
  }

  create() {
    if (!this.form.form.valid) {
      return;
    }
    this.store.dispatch(new CreateAppAction({ ...this.app }));
  }

  cancel() {
    this.router.navigate(['..'], { relativeTo: this.route });
  }

  setAppId() {
    let appId = `${this.app.country.toLocaleLowerCase()}-${this.kebabCase(this.app.title)}`;
    if (this.app.app_type === AppTypes.ENTERPRISE) {
      appId = `em-${appId}`;
    }
    this.app.app_id = appId;
  }

  setDashboardEmail() {
    if (this.app.dashboard_email_address) {
      const currentEmail = this.app.dashboard_email_address.trim();
      if (!(currentEmail.endsWith('@ourcityapps.com') || currentEmail.endsWith('@rogerth.at'))) {
        return;
      }
    }

    if (this.app.title) {
      const appTitle = this.kebabCase(this.app.title);
      if (this.app.app_type === AppTypes.CITY_APP) {
        this.app.dashboard_email_address = `${appTitle}@ourcityapps.com`;
      } else {
        this.app.dashboard_email_address = `${appTitle}@rogerth.at`;
      }
    }
  }

  toggleNewsStream(e: MatSlideToggleChange) {
    if (e.checked) {
      this.app.news_stream = { type: NewsStreamTypes.CITY };
    } else {
      this.app.news_stream = null;
    }
  }

  kebabCase = (string: string) => string.replace(/\s+/g, '-').toLowerCase();
}
