import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output } from '@angular/core';
import { TranslateService } from '@ngx-translate/core';
import { filter } from 'rxjs/operators';
import { DialogService } from '../../../../../framework/client/dialog';
import { ApiRequestStatus } from '../../../../../framework/client/rpc';
import { AppAsset } from '../../../interfaces';

@Component({
  selector: 'rcc-app-asset-list',
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: 'app-asset-list.component.html',
  styleUrls: [ 'app-asset-list.component.css' ],
})
export class AppAssetListComponent {
  @Input() assets: AppAsset[];
  @Input() allowEdit: boolean;
  @Input() status: ApiRequestStatus;
  @Output() remove = new EventEmitter<AppAsset>();
  typeStrings = {
    ChatBackgroundImage: 'rcc.chat_background_image',
  };

  constructor(private translate: TranslateService, private dialogService: DialogService) {
  }

  confirmDelete(asset: AppAsset) {
    const options = {
      title: this.translate.instant('rcc.confirmation'),
      message: this.translate.instant('rcc.confirm_delete_resource'),
      ok: this.translate.instant('rcc.yes'),
      cancel: this.translate.instant('rcc.no'),
    };
    this.dialogService.openConfirm(options).afterClosed().pipe(filter(confirmed => confirmed === true))
      .subscribe(() => this.remove.emit(asset));
  }
}
