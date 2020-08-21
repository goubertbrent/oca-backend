import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output } from '@angular/core';
import { FormControl, NgForm } from '@angular/forms';
import { ApiRequestStatus } from '../../../../../framework/client/rpc';
import {
  APP_TYPES,
  AppTypes,
  EMBEDDED_APP_TAGS,
  EMBEDDED_APP_TYPES,
  EmbeddedApp,
  SaveEmbeddedApp,
} from '../../../interfaces';
import { getFileReaderResult } from '../../../util';

@Component({
  selector: 'rcc-embedded-app-detail',
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: 'embedded-app-detail.component.html',
})
export class EmbeddedAppDetailComponent {
  urlRegexFormControl = new FormControl();
  selectedFile: File | null = null;
  embeddedAppTypes = EMBEDDED_APP_TAGS;
  types = EMBEDDED_APP_TYPES;
  appTypes = APP_TYPES;
  filebase64: string | null;

  @Input() set embeddedApp(value: EmbeddedApp | SaveEmbeddedApp) {
    this._embeddedApp = { ...value };
  }

  get embeddedApp() {
    return this._embeddedApp;
  }

  @Input() status: ApiRequestStatus;
  @Input() update = false;
  @Output() save = new EventEmitter<SaveEmbeddedApp>();

  private _embeddedApp: EmbeddedApp | SaveEmbeddedApp;

  get servingUrl() {
    return (<EmbeddedApp>this.embeddedApp).serving_url ? (<EmbeddedApp>this.embeddedApp).serving_url : null;
  }

  removeUrlRegex(regex: string) {
    this.embeddedApp.url_regexes = this.embeddedApp.url_regexes.filter(u => u !== regex);
  }

  addUrlRegex(regex: string | null) {
    if (regex) {
      this.embeddedApp.url_regexes = [ ...this.embeddedApp.url_regexes, regex ];
    }
    this.urlRegexFormControl.reset();
  }

  submit(form: NgForm) {
    if (form.form.valid && !this.status.loading) {
      this.save.emit({
        file: this.filebase64,
        name: this.embeddedApp.name,
        tags: this.embeddedApp.tags,
        url_regexes: this.embeddedApp.url_regexes,
        description: this.embeddedApp.description,
        title: this.embeddedApp.title,
        types: this.embeddedApp.types,
        app_types: this.embeddedApp.app_types,
      });
    }
  }

  setFile(input: Event) {
    const files = (<HTMLInputElement>input.target).files;
    this.selectedFile = files && files.length ? files[ 0 ] : null;
    if (this.selectedFile) {
      const fileReader = new FileReader();
      fileReader.readAsDataURL(this.selectedFile);
      fileReader.onload = () => {
        if (fileReader.result) {
          this.filebase64 = getFileReaderResult(fileReader);
        }
      };
    }
  }
}
