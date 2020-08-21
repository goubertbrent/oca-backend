import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output, ViewEncapsulation } from '@angular/core';
import { ApiRequestStatus } from '../../../../framework/client/rpc';
import { AppSearchParameters, AppSearchResult } from '../../interfaces';
import { ConsoleConfig } from '../../services';

@Component({
  selector: 'rcc-app-list',
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.Emulated,
  templateUrl: 'app-list.component.html',
  styleUrls: [ 'app-list.component.css' ],
})
export class AppListComponent {
  @Input() apps: AppSearchResult[];
  @Input() appsStatus: ApiRequestStatus;
  @Output() onSearch = new EventEmitter<AppSearchParameters>();

  private _searchParams: AppSearchParameters;

  get searchParams() {
    return this._searchParams;
  }

  @Input() set searchParams(value: AppSearchParameters) {
    this._searchParams = { ...value };
  }

  getImageUrl(app: AppSearchResult) {
    return `url(${ConsoleConfig.BUILDSERVER_URL}/image/app/${app.app_id}/thumbnail)`;
  }

  search() {
    this.onSearch.emit({ ...this.searchParams });
  }
}
