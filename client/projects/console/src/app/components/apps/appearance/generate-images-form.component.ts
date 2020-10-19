import { ChangeDetectionStrategy, ChangeDetectorRef, Component, ElementRef, EventEmitter, Input, Output, ViewChild } from '@angular/core';
import { TranslateService } from '@ngx-translate/core';
import { ApiRequestStatus } from '../../../../../framework/client/rpc';
import { AppImageInfo, CheckListItem, GenerateImagesPayload } from '../../../interfaces';
import { ImageSelector } from '../../../util';

@Component({
  selector: 'rcc-appearance-generate-images-form',
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: 'generate-images-form.component.html',
})
export class AppearanceGenerateImagesFormComponent extends ImageSelector {
  payload: GenerateImagesPayload = {
    file: null,
    types: [],
  };
  private excludedImages = ['about_footer'];


  @Input() status: ApiRequestStatus;
  @Input() generateStatus: ApiRequestStatus;

  @Output() generate = new EventEmitter<GenerateImagesPayload>();

  @ViewChild('file', { static: true }) file: ElementRef;

  get imagesInfo(): AppImageInfo[] {
    return this._imagesInfo;
  }

  @Input() set imagesInfo(info: AppImageInfo[]) {
    if (info) {
      this._imagesInfo = info.filter(i => !this.excludedImages.includes(i.type));
      this.imagesList = this.imagesInfo.map(i => ({
        label: this.translate.stream(`rcc.${i.type}`),
        value: i.type,
      }));
      this.payload.types = this.imagesList.map(item => item.value);
    }
  }
  imagesList: CheckListItem[];
  errorMessage: string;

  private imageWidth = 1024;
  private imageHeight = 1024;
  private _imagesInfo: AppImageInfo[];

  constructor(private translate: TranslateService,
              private cdRef: ChangeDetectorRef) {
    super();
  }

  onFileSelected(file: File) {
    if (file) {
      this.payload.file = file;
      this.validateImage(file, this.imageWidth, this.imageHeight);
    }
  }

  onImageValidated(success: boolean, data: string) {
    if (success) {
      this.errorMessage = '';
    } else {
      this.errorMessage = this.translate.instant('rcc.invalid_dimensions_max_x_allowed', {
        width: this.imageWidth,
        height: this.imageHeight,
      });
      this.file.nativeElement.value = '';
    }
    this.cdRef.markForCheck();
  }

  submit() {
    this.generate.emit(this.payload);
  }

}
