import { ChangeDetectionStrategy, Component } from '@angular/core';
import { MatDialogConfig } from '@angular/material/dialog';
import { TranslateService } from '@ngx-translate/core';
import { DialogService } from '../../../../framework/client/dialog';
import { AutoConnectedService, Language, LANGUAGES } from '../../interfaces';
import { cloneDeep, makeNgModelProvider } from '../../util';
import { EditAutoConnectedServiceDialogComponent } from './edit-acs-dialog.component';

@Component({
  selector: 'rcc-auto-connected-services',
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: 'auto-connected-services.component.html',
  providers: [ makeNgModelProvider(AutoConnectedServicesComponent) ],
})
export class AutoConnectedServicesComponent {
  languages = LANGUAGES;
  private onTouched: () => void;
  private onChange: (_: any) => void;

  constructor(private dialogService: DialogService,
              private translate: TranslateService) {
  }

  get autoConnectedServices(): AutoConnectedService[] {
    return this.value;
  }

  set autoConnectedServices(value: AutoConnectedService[]) {
    this.value = value; // From AbstractControlValueAccessor
  }

  // todo: Temporary fix, this should be in AbstractControlValueAccessor
  private _value: any = null;

  get value(): any {
    return this._value;
  }

  set value(v: any) {
    if (v !== this._value) {
      this._value = cloneDeep(v);
      this.onChange(v);
    }
  }

  writeValue(value: any) {
    this._value = value;
    if (this.onChange) {
      this.onChange(value);
    }
  }

  registerOnChange(fn: (_: any) => void): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: () => void): void {
    this.onTouched = fn;
  }

  locales(array: string[]) {
    return array.map(langCode => (<Language>this.languages.find(lang => lang.code === langCode)).name);
  }

  addAcs() {
    const acs: AutoConnectedService = {
      service_identity_email: '',
      removable: false,
      local: [],
      service_roles: [],
    };
    const options: MatDialogConfig = {
      data: {
        isNew: true,
        acs: acs,
      },
    };
    const sub = this.dialogService.open(EditAutoConnectedServiceDialogComponent, options)
      .afterClosed()
      .subscribe((result: AutoConnectedService | null) => {
        if (result) {
          this.autoConnectedServices = [ ...this.autoConnectedServices, result ];
        }
        sub.unsubscribe();
      });
  }

  editAcs(acs: AutoConnectedService) {
    const options: MatDialogConfig = {
      data: {
        isNew: false,
        acs: acs,
      },
    };
    const sub = this.dialogService.open(EditAutoConnectedServiceDialogComponent, options)
      .afterClosed()
      .subscribe((result: AutoConnectedService | null) => {
        if (result) {
          this.autoConnectedServices = [
            ...this.autoConnectedServices.filter(a => a.service_identity_email !== acs.service_identity_email),
            result,
          ];
        }
        sub.unsubscribe();
      });
  }

  confirmRemoveService(acs: AutoConnectedService) {
    const service = acs.service_identity_email;
    const config = {
      title: this.translate.instant('rcc.remove_auto_connected_service'),
      message: this.translate.instant('rcc.are_you_sure_you_want_to_remove_x_acs', { service: service }),
      ok: this.translate.instant('rcc.yes'),
      cancel: this.translate.instant('rcc.no'),
    };
    this.dialogService.openConfirm(config).afterClosed().subscribe((confirmed: boolean) => {
      if (confirmed) {
        this.autoConnectedServices = [ ...this.autoConnectedServices.filter(a => a !== acs) ];
      }
    });
  }

}
