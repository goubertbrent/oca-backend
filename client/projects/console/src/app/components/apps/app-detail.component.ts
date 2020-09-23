import { ChangeDetectionStrategy, Component, OnDestroy, OnInit } from '@angular/core';
import { ActivatedRoute, Router, UrlSegment } from '@angular/router';
import { select, Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { Observable, Subscription } from 'rxjs';
import { map } from 'rxjs/operators';
import { DialogService, PromptDialogResult } from '../../../../framework/client/dialog';
import { SecondarySidebarItem, SidebarTitle } from '../../../../framework/client/nav/sidebar';
import { AddToolbarItemAction, RemoveToolbarItemAction, ToolbarItem, ToolbarItemTypes } from '../../../../framework/client/nav/toolbar';
import { ApiError, ApiRequestStatus } from '../../../../framework/client/rpc';
import * as actions from '../../actions';
import * as states from '../../console.state';
import { getApp, getRevertChangesStatus, getSaveChangesStatus } from '../../console.state';
import { App, GitStatus } from '../../interfaces';
import { filterNull } from '../../ngrx';
import { ConsoleConfig } from '../../services';

@Component({
  selector: 'rcc-app-detail',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <secondary-sidenav [sidebarItems]="sidebarItems" [sidebarTitle]="title$ | async"></secondary-sidenav>`,
})
export class AppDetailComponent implements OnInit, OnDestroy {
  sidebarItems: SecondarySidebarItem[] = [{
    label: 'rcc.settings',
    icon: 'settings',
    route: 'settings',
  }, {
    label: 'rcc.builds',
    icon: 'build',
    route: 'builds',
  }, {
    label: 'rcc.assets',
    icon: 'photo_library',
    route: 'assets',
  }, {
    label: 'rcc.store_listing',
    icon: 'description',
    route: 'store-listing',
  }, {
    label: 'rcc.appearance',
    icon: 'looks',
    route: 'appearance',
  }];
  title$: Observable<SidebarTitle>;

  private subs: Subscription[];

  constructor(private store: Store,
              private route: ActivatedRoute,
              private router: Router,
              private dialogService: DialogService,
              private translate: TranslateService) {
  }

  ngOnInit() {
    const appId = this.route.snapshot.params[ 'appId' ];
    this.store.dispatch(new actions.GetAppAction(appId));
    this.subs = [this.store.pipe(select(states.getApp)).subscribe(this._appChanged.bind(this)),
      this.store.pipe(select(getRevertChangesStatus)).subscribe(this._revertChanged.bind(this)),
      this.store.pipe(select(getSaveChangesStatus)).subscribe(this._saveChanged.bind(this))];
    this.title$ = this.store.pipe(select(getApp), filterNull(), map(app => ({
      label: app.title,
      isTranslation: false,
      imageUrl: `${ConsoleConfig.BUILDSERVER_URL}/image/app/${app.app_id}/thumbnail`,
    } as SidebarTitle)));
  }

  ngOnDestroy() {
    for (const s of this.subs) {
      s.unsubscribe();
    }
  }

  getToolbarItems(loading: boolean): ToolbarItem[] {
    return [{
      id: 'publish_changes',
      type: ToolbarItemTypes.BUTTON,
      label: 'rcc.publish',
      disabled: loading,
      onclick: this.publish.bind(this),
      icon: 'publish',

    }, {
      id: 'revert_changes',
      type: ToolbarItemTypes.BUTTON,
      label: 'rcc.revert',
      disabled: loading,
      onclick: this.revert.bind(this),
      icon: 'undo',
    }];
  }

  setToolbarItems(loading: boolean) {
    const items = this.getToolbarItems(loading);
    for (const item of items) {
      this.store.dispatch(new RemoveToolbarItemAction(item.id));
    }
    for (const item of items) {
      this.store.dispatch(new AddToolbarItemAction(item));
    }
  }

  publish() {
    const options = {
      ok: this.translate.instant('rcc.publish'),
      cancel: this.translate.instant('rcc.cancel'),
      title: this.translate.instant('rcc.save_changes'),
      message: this.translate.instant('rcc.save_changes_to_app_message'),
    };
    this.dialogService.openPrompt(options).afterClosed()
      .subscribe((result: PromptDialogResult) => {
        if (result && result.submitted) {
          this.setToolbarItems.bind(this)(true);
          this.store.dispatch(new actions.SaveAppChangesAction({ comment: result.value }));
        }
      });
  }

  revert() {
    const options = {
      ok: this.translate.instant('rcc.yes'),
      cancel: this.translate.instant('rcc.cancel'),
      title: this.translate.instant('rcc.revert_changes'),
      message: this.translate.instant('rcc.are_you_sure_you_want_to_revert_changes'),
    };
    const sub = this.dialogService.openConfirm(options).afterClosed()
      .subscribe((confirmed: boolean) => {
        if (confirmed) {
          this.setToolbarItems.bind(this)(true);
          this.store.dispatch(new actions.RevertAppChangesAction());
        }
        sub.unsubscribe();
      });
  }

  private _saveChanged(status: ApiRequestStatus) {
    if (status.error) {
      this._showAlert('rcc.error_could_not_save_changes', status);
    }
  }

  private _revertChanged(status: ApiRequestStatus) {
    if (status.error) {
      this._showAlert('rcc.error_could_not_revert', status);
    } else if (status.success) {
      // goto app overview to force a refresh
      this.router.navigate([this.route.snapshot.url.map((u: UrlSegment) => u.path).join('/')]);
    }
  }

  private _showAlert(translationKey: string, status: ApiRequestStatus) {
    const options = {
      ok: this.translate.instant('rcc.ok'),
      message: this.translate.instant(translationKey, { error: (<ApiError>status.error).error }),
      title: this.translate.instant('rcc.error'),
    };
    this.dialogService.openAlert(options);
  }

  private _appChanged(app: App | null) {
    if (!app) {
      return;
    }
    this.store.dispatch(new actions.GetRogerthatAppAction({ appId: app.app_id }));
    const toolbarItems = this.getToolbarItems.bind(this)(false);
    for (const item of toolbarItems) {
      if (app.git_status === GitStatus.DRAFT) {
        this.store.dispatch(new AddToolbarItemAction(item));
      } else {
        this.store.dispatch(new RemoveToolbarItemAction(item.id));
      }
    }
  }
}
