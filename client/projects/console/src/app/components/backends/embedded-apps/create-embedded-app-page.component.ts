import { ChangeDetectionStrategy, Component, OnDestroy, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { Actions, ofType } from '@ngrx/effects';
import { select, Store } from '@ngrx/store';
import { Observable, Subscription } from 'rxjs';
import { ApiRequestStatus } from '../../../../../framework/client/rpc';
import { BackendsActionTypes, CreateEmbeddedAppAction } from '../../../actions';
import { createEmbeddedAppStatus } from '../../../console.state';
import { AppTypes, EmbeddedAppTag, SaveEmbeddedApp } from '../../../interfaces';

@Component({
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <mat-toolbar>
      <button mat-icon-button [routerLink]="['..']">
        <mat-icon>arrow_back</mat-icon>
      </button>
      <h2>{{ 'rcc.create_embedded_app' | translate }}</h2>
    </mat-toolbar>
    <div class="default-component-margin-full">
      <rcc-embedded-app-detail [embeddedApp]="embeddedApp" [status]="createStatus$ | async"
                               (save)="onSave($event)"></rcc-embedded-app-detail>
    </div>`,
})
export class CreateEmbeddedAppPageComponent implements OnInit, OnDestroy {
  embeddedApp: SaveEmbeddedApp = {
    tags: [ EmbeddedAppTag.PAYMENTS ],
    name: '',
    file: null,
    url_regexes: [],
    types: [],
    title: null,
    description: null,
    app_types: [AppTypes.CITY_APP],
  };
  createStatus$: Observable<ApiRequestStatus>;

  private _createSubscription: Subscription;

  constructor(private store: Store,
              private actions$: Actions,
              private router: Router,
              private route: ActivatedRoute) {
  }

  ngOnInit() {
    this.createStatus$ = this.store.pipe(select(createEmbeddedAppStatus));
    this._createSubscription = this.actions$.pipe(
      ofType(BackendsActionTypes.CREATE_EMBEDDED_APP_COMPLETE),
    ).subscribe(() => this.router.navigate([ '..' ], { relativeTo: this.route }));
  }

  ngOnDestroy() {
    this._createSubscription.unsubscribe();
  }

  onSave(data: SaveEmbeddedApp) {
    this.store.dispatch(new CreateEmbeddedAppAction(data));
  }
}
