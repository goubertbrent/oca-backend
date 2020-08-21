import { ChangeDetectionStrategy, Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { FormControl } from '@angular/forms';
import { MatChipInputEvent } from '@angular/material/chips';
import { Observable } from 'rxjs';
import { map, startWith } from 'rxjs/operators';
import { ApiRequestStatus } from '../../../../../framework/client/rpc';
import { EditAppAssetPayload, RogerthatApp } from '../../../interfaces';
import { FileSelector } from '../../../util';

@Component({
  selector: 'rcc-app-resource',
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: 'app-resource.component.html',
})
export class AppResourceComponent extends FileSelector implements OnInit {
  appFormControl = new FormControl();
  filteredApps: Observable<RogerthatApp[]>;
  @Input() edit: boolean;
  @Input() allowCreateDefault: boolean;
  @Input() apps: RogerthatApp[] = [];
  @Input() status: ApiRequestStatus;
  @Output() save = new EventEmitter<EditAppAssetPayload>();

  private _asset: EditAppAssetPayload;

  get asset(): EditAppAssetPayload {
    return this._asset;
  }

  @Input() set asset(value: EditAppAssetPayload) {
    this._asset = JSON.parse(JSON.stringify(value));
  }

  ngOnInit() {
    this.filteredApps = this.appFormControl.valueChanges.pipe(
      startWith(''),
      map(val => val ? this.filterApps(val) : this.apps.slice()),
    );
  }

  addApp(event: MatChipInputEvent) {
    if (!this.asset.app_ids.includes(event.value) && this.getAppName(event.value)) {
      this.asset.app_ids = [ ...this.asset.app_ids, event.value ];
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

  removeApp(appId: string) {
    this.asset.app_ids = this.asset.app_ids.filter(a => a !== appId);
  }

  onFileSelected(file: File) {
    this._asset.file = file;
  }

  submit() {
    this.save.emit(this.asset);
  }

  private filterApps(val: string): RogerthatApp[] {
    const re = new RegExp(val, 'gi');
    return this.apps.filter(app => !this.asset.app_ids.includes(app.id) && (re.test(app.name) || re.test(app.id)));
  }
}
