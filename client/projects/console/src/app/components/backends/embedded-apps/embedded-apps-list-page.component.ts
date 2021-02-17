import { ChangeDetectionStrategy, Component, OnInit } from '@angular/core';
import { select, Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { Observable } from 'rxjs';
import { DialogService } from '../../../../../framework/client/dialog';
import { ApiRequestStatus } from '../../../../../framework/client/rpc';
import { ListEmbeddedAppsAction, RemoveEmbeddedAppAction } from '../../../actions';
import { deleteEmbeddedAppStatus, getEmbeddedApps, listEmbeddedAppsStatus } from '../../../console.state';
import { EmbeddedApp } from '../../../interfaces/embedded-apps';

@Component({
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: 'embedded-apps-list-page.component.html',
})
export class EmbeddedAppsListPageComponent implements OnInit {
  embeddedApps$: Observable<EmbeddedApp[]>;
  listStatus$: Observable<ApiRequestStatus>;
  deleteStatus$: Observable<ApiRequestStatus>;

  constructor(private store: Store,
              private translate: TranslateService,
              private dialogService: DialogService) {
  }

  ngOnInit() {
    this.store.dispatch(new ListEmbeddedAppsAction());
    this.embeddedApps$ = this.store.pipe(select(getEmbeddedApps));
    this.listStatus$ = this.store.pipe(select(listEmbeddedAppsStatus));
    this.deleteStatus$ = this.store.pipe(select(deleteEmbeddedAppStatus));
  }

  confirmRemove(event: Event, embeddedApp: EmbeddedApp) {
    event.stopPropagation();
    event.preventDefault();
    const config = {
      title: this.translate.instant('rcc.remove_embedded_app'),
      message: this.translate.instant('rcc.are_you_sure_you_want_to_delete_embedded_app', { app: embeddedApp.name }),
      ok: this.translate.instant('rcc.yes'),
      cancel: this.translate.instant('rcc.no'),
    };
    this.dialogService.openConfirm(config).afterClosed().subscribe((confirmed: boolean) => {
      if (confirmed) {
        this.store.dispatch(new RemoveEmbeddedAppAction((embeddedApp.name)));
      }
    });
  }
}
