import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  ElementRef,
  EventEmitter,
  Output,
  ViewChild,
  ViewEncapsulation,
} from '@angular/core';
import { FormControl, FormGroup, Validators } from '@angular/forms';
import { TranslateService } from '@ngx-translate/core';
import { ImageSelector } from '../../../util';
import { UpdateNewsImagePayload } from '../news';

@Component({
  selector: 'rcc-news-group-form',
  templateUrl: 'news-group-form.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
})
export class NewsGroupFormComponent extends ImageSelector {
  @ViewChild('file', { static: true }) file: ElementRef;
  @Output() save = new EventEmitter<UpdateNewsImagePayload>();
  errorMessage: string;
  selectedFile: File | null = null;
  formGroup = new FormGroup({
    file: new FormControl(null, Validators.required),
  });

  constructor(private translate: TranslateService,
              private cdRef: ChangeDetectorRef) {
    super();
  }

  onFileSelected(file: File) {
    this.selectedFile = file;
  }

  onImageValidated(success: boolean) {
    if (success) {
      this.errorMessage = '';
    } else {
      this.errorMessage = 'File was not valid...';
      this.formGroup.controls.file.reset();
    }
    this.cdRef.markForCheck();
  }

  submit() {
    if (this.formGroup.valid) {
      this.save.emit({ file: this.selectedFile });
    }
  }
}
