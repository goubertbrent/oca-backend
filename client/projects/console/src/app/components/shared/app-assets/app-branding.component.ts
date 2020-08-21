import { ChangeDetectionStrategy, Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { FormControl } from '@angular/forms';
import { MatChipInputEvent } from '@angular/material/chips';
import { Observable } from 'rxjs';
import { map, startWith } from 'rxjs/operators';
import { ApiRequestStatus } from '../../../../../framework/client/rpc';
import { CreateDefaultBrandingPayload, DEFAULT_BRANDING_TYPES, RogerthatApp } from '../../../interfaces';
import { FileSelector } from '../../../util';

@Component({
  selector: 'rcc-app-branding',
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: 'app-branding.component.html',
  styles: [ `mat-select, mat-form-field {
    min-width: 200px;
  }` ],
})
export class AppBrandingComponent extends FileSelector implements OnInit {
  appFormControl = new FormControl();
  filteredApps: Observable<RogerthatApp[]>;
  BRANDING_TYPES = DEFAULT_BRANDING_TYPES;
  @Input() edit: boolean;
  @Input() allowCreateDefault: boolean;
  @Input() apps: RogerthatApp[] = [];
  @Input() status: ApiRequestStatus;
  @Output() save = new EventEmitter<CreateDefaultBrandingPayload>();

  private _branding: CreateDefaultBrandingPayload;

  get branding(): CreateDefaultBrandingPayload {
    return this._branding;
  }

  @Input() set branding(value: CreateDefaultBrandingPayload) {
    this._branding = { ...value };
  }

  ngOnInit() {
    this.filteredApps = this.appFormControl.valueChanges.pipe(
      startWith(''),
      map(val => val ? this.filterApps(val) : this.apps.slice()),
    );
  }

  addApp(event: MatChipInputEvent) {
    if (!this.branding.app_ids.includes(event.value) && this.getAppName(event.value)) {
      this.branding.app_ids = [ ...this.branding.app_ids, event.value ];
    }
    this.appFormControl.reset();
  }

  getAppName(appId: string) {
    const app = this.apps.find(a => a.id === appId);
    if (app) {
      return app.name;
    } else {
      return ''; // apps probably not loaded yet
    }
  }

  getHint() {
    const type = DEFAULT_BRANDING_TYPES.find(b => b.value === this.branding.branding_type);
    return type ? type.hint : null;
  }

  removeApp(appId: string) {
    this.branding.app_ids = this.branding.app_ids.filter(a => a !== appId);
  }

  onFileSelected(file: File) {
    this.branding.file = file;
  }

  submit() {
    this.save.emit({ ...this.branding });
  }

  private filterApps(val: string): RogerthatApp[] {
    const re = new RegExp(val, 'gi');
    return this.apps.filter(app => !this.branding.app_ids.includes(app.id) && (re.test(app.name) || re.test(app.id)));
  }
}
