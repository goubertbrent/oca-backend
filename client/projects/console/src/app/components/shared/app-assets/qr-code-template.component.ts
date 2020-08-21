import { ChangeDetectionStrategy, ChangeDetectorRef, Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { ApiRequestStatus } from '../../../../../framework/client/rpc';
import { QrCodeTemplate } from '../../../interfaces';
import { FileSelector } from '../../../util';

@Component({
  selector: 'rcc-qr-code-template',
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: 'qr-code-template.component.html',
})
export class QrCodeTemplateComponent extends FileSelector implements OnInit {
  qrCodeTemplate: QrCodeTemplate;
  @Input() status: ApiRequestStatus;
  @Input() createStatus: ApiRequestStatus;
  @Output() create = new EventEmitter<QrCodeTemplate>();

  constructor(private cdRef: ChangeDetectorRef) {
    super();
  }

  ngOnInit() {
    this.qrCodeTemplate = {
      description: '',
      body_color: '#000000',
      file: null,
      is_default: true,
    };
  }

  submit() {
    this.create.emit(this.qrCodeTemplate);
  }

  onFileSelected(file: File) {
    if (!file) {
      return;
    }
    this.qrCodeTemplate.file = null;
    this.readFile(file);
  }

  onReadCompleted(data: string) {
    this.qrCodeTemplate.file = data;
    this.cdRef.markForCheck();
  }
}
