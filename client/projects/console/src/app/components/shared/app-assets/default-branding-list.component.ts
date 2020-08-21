import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output, ViewEncapsulation } from '@angular/core';
import { TranslateService } from '@ngx-translate/core';
import { DialogService } from '../../../../../framework/client/dialog';
import { ApiRequestStatus } from '../../../../../framework/client/rpc';
import { DefaultBranding } from '../../../interfaces';

@Component({
  selector: 'rcc-default-branding-list',
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.Emulated,
  templateUrl: 'default-branding-list.component.html',
  styles: [`.default-branding-card {
    display: inline-block;
    width: 250px;
    margin: 16px;
  }`],
})
export class DefaultBrandingListComponent {
  @Input() brandings: DefaultBranding[];
  @Input() allowEdit: boolean;
  @Input() status: ApiRequestStatus;
  @Output() remove = new EventEmitter<DefaultBranding>();
  typeStrings = {
    'DefaultBirthdayMessageBranding': 'rcc.default_birthday_message_branding',
  };

  constructor(private translate: TranslateService,
              private dialogService: DialogService) {
  }

  getDownloadUrl(branding: DefaultBranding) {
    return `/unauthenticated/mobi/branding/${branding.branding}`;
  }

  confirmDelete(branding: DefaultBranding) {
    const config = {
      title: this.translate.instant('rcc.confirmation'),
      message: this.translate.instant('rcc.confirm_delete_default_branding'),
      ok: this.translate.instant('rcc.yes'),
      cancel: this.translate.instant('rcc.no'),
    };
    this.dialogService.openConfirm(config).afterClosed().subscribe(confirmed => {
      if (confirmed) {
        this.remove.emit(branding);
      }
    });
  }
}
