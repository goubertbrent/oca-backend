import { ChangeDetectionStrategy, ChangeDetectorRef, Component, forwardRef } from '@angular/core';
import { ControlValueAccessor, NG_VALUE_ACCESSOR } from '@angular/forms';
import { MatDialogConfig } from '@angular/material/dialog';
import { TranslateService } from '@ngx-translate/core';
import { DialogService } from '../../../../../framework/client/dialog';
import { AutoConnectedService } from '../communities';
import { EditAutoConnectedServiceDialogComponent } from '../edit-acs-dialog/edit-acs-dialog.component';

@Component({
  selector: 'rcc-auto-connected-services',
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: 'auto-connected-services.component.html',
  providers: [{
    provide: NG_VALUE_ACCESSOR,
    useExisting: forwardRef(() => AutoConnectedServicesComponent),
    multi: true,
  }],
  styles: [`.acs-item {
    width: 560px;
  }`],
})
export class AutoConnectedServicesComponent implements ControlValueAccessor {
  value: AutoConnectedService[] = [];
  private onTouched: () => void;
  private onChange: (_: any) => void;

  constructor(private dialogService: DialogService,
              private changeDetectorRef: ChangeDetectorRef,
              private translate: TranslateService) {
  }

  setValue(v: AutoConnectedService[]) {
    this.value = v;
    if (this.value && this.onChange) {
      this.onChange(v);
    }
    this.changeDetectorRef.markForCheck();
  }

  writeValue(value: AutoConnectedService[]) {
    this.setValue(value);
  }

  registerOnChange(fn: (_: any) => void): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: () => void): void {
    this.onTouched = fn;
  }

  addAcs() {
    const acs: AutoConnectedService = {
      service_email: '',
      removable: false,
    };
    const options: MatDialogConfig = {
      data: {
        isNew: true,
        acs,
      },
    };
    this.dialogService.open(EditAutoConnectedServiceDialogComponent, options)
      .afterClosed()
      .subscribe((result: AutoConnectedService | null) => {
        if (result) {
          this.setValue([...this.value, result]);
        }
      });
  }

  editAcs(acs: AutoConnectedService) {
    const options: MatDialogConfig = {
      data: {
        isNew: false,
        acs,
      },
    };
    this.dialogService.open(EditAutoConnectedServiceDialogComponent, options)
      .afterClosed()
      .subscribe((result: AutoConnectedService | null) => {
        if (result) {
          this.setValue([...this.value.filter(a => a.service_email !== acs.service_email), result]);
        }
      });
  }

  confirmRemoveService(acs: AutoConnectedService) {
    const service = acs.service_email;
    const config = {
      title: this.translate.instant('rcc.remove_auto_connected_service'),
      message: this.translate.instant('rcc.are_you_sure_you_want_to_remove_x_acs', { service }),
      ok: this.translate.instant('rcc.yes'),
      cancel: this.translate.instant('rcc.no'),
    };
    this.dialogService.openConfirm(config).afterClosed().subscribe((confirmed: boolean) => {
      if (confirmed) {
        this.setValue(this.value.filter(a => a !== acs));
      }
    });
  }

}
