import { ChangeDetectionStrategy, ChangeDetectorRef, Component } from '@angular/core';
import { ControlValueAccessor, FormControl, Validators } from '@angular/forms';
import { MatChipInputEvent } from '@angular/material/chips';
import { TranslateService } from '@ngx-translate/core';
import { DialogService } from '../../../../framework/client/dialog';
import { SERVICE_IDENTITY_REGEX } from '../../constants';
import { cloneDeep, makeNgModelProvider } from '../../util';

@Component({
  selector: 'rcc-admin-services',
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: 'admin-services.component.html',
  providers: [ makeNgModelProvider(AdminServicesComponent) ],
})
export class AdminServicesComponent implements ControlValueAccessor {
  adminServiceFormControl = new FormControl(null, Validators.pattern(SERVICE_IDENTITY_REGEX));
  private onTouchedCallback: () => void;
  private onChangeCallback: (_: any) => void;

  constructor(private translate: TranslateService,
              private dialogService: DialogService,
              private cdRef: ChangeDetectorRef) {
  }

  private _adminServices: string[];

  get adminServices() {
    return this._adminServices;
  }

  set adminServices(value: string[]) {
    this._adminServices = cloneDeep(value);
    if (this.onChangeCallback) {
      this.onChangeCallback(value);
    }
  }

  public writeValue(obj: any): void {
    this.adminServices = obj;
    this.cdRef.markForCheck();
  }

  public registerOnChange(fn: any): void {
    this.onChangeCallback = fn;
  }

  public registerOnTouched(fn: any): void {
    this.onTouchedCallback = fn;
  }

  addAdminService(event: MatChipInputEvent) {
    if (!this.adminServiceFormControl.valid) {
      // Ensure error message is shown
      this.adminServiceFormControl.markAsTouched();
      return;
    }
    if (!this.adminServices.includes(event.value)) {
      this.adminServices = [ ...this.adminServices, event.value ];
    }
    this.adminServiceFormControl.reset();
  }

  confirmRemoveService(adminService: string) {
    const config = {
      title: this.translate.instant('rcc.remove_admin_service'),
      message: this.translate.instant('rcc.are_you_sure_you_want_to_remove_x_admin_service', { service: adminService }),
      ok: this.translate.instant('rcc.yes'),
      cancel: this.translate.instant('rcc.no'),
    };
    this.dialogService.openConfirm(config).afterClosed().subscribe((confirmed: boolean) => {
      if (confirmed) {
        this.adminServices = this.adminServices.filter(a => a !== adminService);
      }
    });
  }

}
