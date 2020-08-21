import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output, ViewEncapsulation } from '@angular/core';
import { TranslateService } from '@ngx-translate/core';
import { DialogService } from '../../../../../framework/client/dialog';
import { App, QrCodeTemplate } from '../../../interfaces';
import { ConsoleConfig } from '../../../services';


@Component({
  selector: 'rcc-qr-code-template-list',
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.Emulated,
  templateUrl: 'qr-code-template-list.component.html',
  styleUrls: [ 'qr-code-template-list.component.css' ],
})
export class QrCodeTemplateListComponent {
  @Input() app: App;
  @Input() qrCodeTemplates: QrCodeTemplate[];
  @Output() remove = new EventEmitter<QrCodeTemplate>();

  constructor(private translate: TranslateService,
              private dialogService: DialogService) {
  }


  getImageUrl(template: QrCodeTemplate) {
    const description = encodeURIComponent(template.description);
    if (template.id) {
      // todo when needed
      return '';
    } else {
      return `/console-api/images/apps/${this.app.app_id}/qr-templates/${description}`;
    }
  }

  confirmDelete(template: QrCodeTemplate) {
    const config = {
      title: this.translate.instant('rcc.confirmation'),
      message: this.translate.instant('rcc.confirm_delete_thing', { object: template.description }),
      ok: this.translate.instant('rcc.yes'),
      cancel: this.translate.instant('rcc.no'),
    };
    this.dialogService.openConfirm(config).afterClosed().subscribe((confirmed: boolean) => {
      if (confirmed) {
        this.remove.emit(template);
      }
    });
  }
}
