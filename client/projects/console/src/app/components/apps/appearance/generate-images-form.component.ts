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
import { TranslateService } from '@ngx-translate/core';
import { ApiRequestStatus } from '../../../../../framework/client/rpc';
import { AppImageInfo, CheckListItem, GenerateImagesPayload } from '../../../interfaces';
import { ImageSelector } from '../../../util';

@Component({
  selector: 'rcc-appearance-generate-images-form',
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: 'generate-images-form.component.html',
})
export class AppearanceGenerateImagesFormComponent extends ImageSelector implements OnInit {
  private excludedImages = [ 'about_footer' ];

  @Input() set imagesInfo(info: AppImageInfo[]) {
    if (info) {
      this._imagesInfo = info.filter(i => !this.excludedImages.includes(i.type));
      this.imagesList = this.imagesInfo.map(i => <CheckListItem>{
        label: this.translate.stream(`rcc.${ i.type }`),
        value: i.type,
        checked: true,
      });
    }
  }

  get imagesInfo(): AppImageInfo[] {
    return this._imagesInfo;
  }

  @Input() status: ApiRequestStatus;
  @Input() generateStatus: ApiRequestStatus;

  @Output() generate = new EventEmitter<GenerateImagesPayload>();

  @ViewChild('file', { static: true }) file: ElementRef;

  payload: GenerateImagesPayload;
  imagesList: CheckListItem[];
  errorMessage: string;

  private imageWidth = 1024;
  private imageHeight = 1024;
  private _imagesInfo: AppImageInfo[];

  constructor(private translate: TranslateService,
              private cdRef: ChangeDetectorRef) {
    super();
  }

  ngOnInit() {
    this.payload = <GenerateImagesPayload>{
      file: null,
      types: [],
    };
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

  setImages(items: CheckListItem[]) {
    this.payload.types = items.filter(item => item.checked).map(item => item.value);
  }

  submit() {
    this.generate.emit(this.payload);
  }

}
