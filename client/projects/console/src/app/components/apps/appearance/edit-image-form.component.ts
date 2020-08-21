import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  ElementRef,
  EventEmitter,
  Input,
  OnInit,
  Output,
  ViewChild,
} from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { TranslateService } from '@ngx-translate/core';
import { ApiRequestStatus } from '../../../../../framework/client/rpc';
import { AppImageInfo, UpdateAppImagePayload } from '../../../interfaces';
import { ConsoleConfig } from '../../../services';
import { ImageSelector } from '../../../util';

@Component({
  selector: 'rcc-appearance-edit-image-form',
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: 'edit-image-form.component.html',
})
export class AppearanceEditImageFormComponent extends ImageSelector implements OnInit {
  @ViewChild('file', { static: false }) file: ElementRef;
  @Input() imageInfo: AppImageInfo;
  @Input() status: ApiRequestStatus;
  @Input() appId: string;
  @Output() save = new EventEmitter<UpdateAppImagePayload>();
  errorMessage: string;
  private reloadImage = false;
  private payload: UpdateAppImagePayload;
  private timestamp: string;

  constructor(private translate: TranslateService,
              private cdRef: ChangeDetectorRef,
              private route: ActivatedRoute) {
    super();
  }

  ngOnInit() {
    this.payload = {
      type: '',
      file: null,
    };
    this.reloadImage = this.route.snapshot.queryParams.reloadImage;
  }

  onFileSelected(file: File) {
    this.payload.file = file;
    if (this.payload.file) {
      this.validateImage(file, this.imageInfo.width, this.imageInfo.height);
    }
  }

  onImageValidated(success: boolean) {
    if (success) {
      this.errorMessage = '';
    } else {
      this.errorMessage = this.translate.instant('rcc.invalid_dimensions_max_x_allowed', {
        width: this.imageInfo.width,
        height: this.imageInfo.height,
      });
      this.file.nativeElement.value = '';
    }
    this.cdRef.markForCheck();
  }

  getImageUrl() {
    let url = `${ConsoleConfig.BUILDSERVER_URL}/image/app/${this.appId}/${this.imageInfo.type}`;

    if (this.reloadImage) {
      // because it's the same URL, add the time to force reload
      url += `?_=${this.timestamp}`;
    }

    return url;
  }

  submit() {
    this.payload.type = this.imageInfo.type;
    this.save.emit(this.payload);
  }

}
