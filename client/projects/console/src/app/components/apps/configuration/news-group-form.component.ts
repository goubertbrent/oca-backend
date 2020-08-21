import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  ElementRef,
  EventEmitter,
  OnInit,
  Output,
  ViewChild,
} from '@angular/core';
import { TranslateService } from '@ngx-translate/core';
import { UpdateNewsImagePayload } from '../../../interfaces';
import { ImageSelector } from '../../../util';

@Component({
  selector: 'rcc-news-group-from',
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: 'news-group-form.component.html',
})
export class NewsGroupFormComponent extends ImageSelector implements OnInit {
  @ViewChild('file', { static: true }) file: ElementRef;
  @Output() save = new EventEmitter<UpdateNewsImagePayload>();
  errorMessage: string;
  private payload: UpdateNewsImagePayload;

  constructor(private translate: TranslateService,
              private cdRef: ChangeDetectorRef) {
    super();
  }

  ngOnInit() {
    this.payload = {
      file: null,
    };
  }

  onFileSelected(file: File) {
    this.payload.file = file;
  }

  onImageValidated(success: boolean) {
    if (success) {
      this.errorMessage = '';
    } else {
      this.errorMessage = 'File was not valid...';
      this.file.nativeElement.value = '';
    }
    this.cdRef.markForCheck();
  }

  submit() {
    this.save.emit(this.payload);
  }
}
