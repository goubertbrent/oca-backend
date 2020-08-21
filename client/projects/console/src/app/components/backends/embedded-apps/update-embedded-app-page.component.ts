import { ChangeDetectionStrategy, Component, OnDestroy, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { Actions, ofType } from '@ngrx/effects';
import { select, Store } from '@ngrx/store';
import { Observable, Subscription } from 'rxjs';
import { filterNull } from '../../../ngrx';
import { ApiRequestStatus } from '../../../../../framework/client/rpc';
import { BackendsActionTypes, GetEmbeddedAppAction, UpdateEmbeddedAppAction } from '../../../actions';
import { getEmbeddedApp, getEmbeddedAppStatus, updateEmbeddedAppStatus } from '../../../console.state';
import { EmbeddedApp, SaveEmbeddedApp } from '../../../interfaces';

@Component({
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <mat-toolbar>
      <button mat-icon-button [routerLink]="['..']">
        <mat-icon>arrow_back</mat-icon>
      </button>
      <h2>{{ 'rcc.update_embedded_app' | translate }}</h2>
    </mat-toolbar>
    <div class="default-component-margin-full">
      <rcc-api-request-status [status]="getStatus$ | async"></rcc-api-request-status>
      <rcc-embedded-app-detail [embeddedApp]="embeddedApp$ | async"
                               [update]="true"
                               [status]="updateStatus$ | async"
                               (save)="onSave($event)"></rcc-embedded-app-detail>
    </div>`,
})
export class UpdateEmbeddedAppPageComponent implements OnInit, OnDestroy {
  embeddedApp$: Observable<EmbeddedApp>;
  getStatus$: Observable<ApiRequestStatus>;
  updateStatus$: Observable<ApiRequestStatus>;

  private _updateSubscription: Subscription;

  constructor(private store: Store,
              private actions$: Actions,
              private route: ActivatedRoute,
              private router: Router) {
  }

  ngOnInit() {
    this.embeddedApp$ = this.store.pipe(select(getEmbeddedApp), filterNull());
    this.store.dispatch(new GetEmbeddedAppAction(this.route.snapshot.params.embeddedAppId));
    this.getStatus$ = this.store.pipe(select(getEmbeddedAppStatus));
    this.updateStatus$ = this.store.pipe(select(updateEmbeddedAppStatus));
    this._updateSubscription = this.actions$.pipe(
      ofType(BackendsActionTypes.UPDATE_EMBEDDED_APP_COMPLETE),
    ).subscribe(() => this.router.navigate([ '..' ], { relativeTo: this.route }));
  }

  ngOnDestroy() {
    this._updateSubscription.unsubscribe();
  }

  onSave(data: SaveEmbeddedApp) {
    this.store.dispatch(new UpdateEmbeddedAppAction(data));
  }
}
