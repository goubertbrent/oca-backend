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
import { FormControl } from '@angular/forms';
import { MatChipInputEvent } from '@angular/material/chips';
import { TranslateService } from '@ngx-translate/core';
import { Observable } from 'rxjs';
import { map, startWith } from 'rxjs/operators';
import { ApiRequestStatus } from '../../../../../framework/client/rpc';
import { ASSET_TYPES, COLOR_SCHEMES, CURRENCIES, EmbeddedApp, PaymentProvider, RogerthatApp } from '../../../interfaces';
import { cloneDeep, ImageSelector } from '../../../util';

@Component({
  selector: 'rcc-payment-provider-form',
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: 'payment-provider-form.component.html',
})
export class PaymentProviderFormComponent extends ImageSelector implements OnInit {
  // TODO clean up: remove assetTypes, colorSchemes, background color, text color
  // TODO add currency conversions
  currencies = CURRENCIES;
  assetTypes = ASSET_TYPES;
  colorSchemes = COLOR_SCHEMES;
  fileError: string;
  appFormControl = new FormControl();
  filteredApps: Observable<RogerthatApp[]>;

  @Input() status: ApiRequestStatus;
  @Input() apps: RogerthatApp[];
  @Input() embeddedApplications: EmbeddedApp[];
  @Output() save = new EventEmitter<PaymentProvider>();
  @ViewChild('logo', { static: false }) logo_elem: ElementRef;

  constructor(private translate: TranslateService, private cdRef: ChangeDetectorRef) {
    super();
  }

  private _paymentProvider: PaymentProvider;

  get paymentProvider() {
    return this._paymentProvider;
  }

  @Input()
  set paymentProvider(value: PaymentProvider) {
    this._paymentProvider = cloneDeep(value);
  }

  // todo generic app_ids chips component
  /** app_ids form control */
  ngOnInit() {
    this.filteredApps = this.appFormControl.valueChanges.pipe(
      startWith(''),
      map(val => val ? this.filterApps(val) : this.apps.slice()),
    );
  }

  addApp(event: MatChipInputEvent) {
    if (!this.paymentProvider.app_ids.includes(event.value) && this.getAppName(event.value)) {
      this.paymentProvider.app_ids = [ ...this.paymentProvider.app_ids, event.value ];
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
    this.paymentProvider.app_ids = this.paymentProvider.app_ids.filter(a => a !== appId);
  }

  private filterApps(val: string): RogerthatApp[] {
    const re = new RegExp(val, 'gi');
    return this.apps.filter(app => !this.paymentProvider.app_ids.includes(app.id) && (re.test(app.name) || re.test(app.id)));
  }

  /** end app_ids form control*/


  getCurrency(code: string) {
    const currency = CURRENCIES.find(c => c.code === code);
    return currency ? `${currency.currency} - ${code}` : code;
  }

  addCurrency(event: MatChipInputEvent): void {
    const input = event.input;
    const value = event.value ? event.value.trim() : event.value;
    if (value) {
      this.paymentProvider.currencies = this.paymentProvider.currencies.concat(value);
    }
    if (input) {
      input.value = '';
    }
  }

  removeCurrency(code: string) {
    this.paymentProvider.currencies = this.paymentProvider.currencies.filter(c => c !== code);
  }

  convertLogo() {
    const fileInput: HTMLInputElement = this.logo_elem.nativeElement;
    if (!fileInput.files) {
      return;
    }
    const file = fileInput.files[ 0 ];
    if (!file) {
      this.fileError = this.translate.instant('rcc.please_select_a_file');
    }
    this.validateImageByRatio(file, 1);
  }

  onImageValidated(success: boolean, data: string | null = null) {
    if (success) {
      this.fileError = '';
      // append the mimetype
      this.paymentProvider.logo = `data:image/png;base64,${data}`;
    } else {
      this.fileError = this.translate.instant('rcc.invalid_aspect_ratio', { aspect_ratio: '1:1' });
    }
    this.cdRef.markForCheck();
  }

  getSettings() {
    return JSON.stringify(this.paymentProvider.settings, null, 2);
  }

  setSettings(event: Event) {
    const settings = event.target && (<HTMLInputElement>event.target).value || '{}';
    try {
      this.paymentProvider.settings = JSON.parse(settings);
    } catch (e) {
      console.error('Invalid JSON', settings);
    }
  }

  submit() {
    const result = { ...this.paymentProvider };
    if (result.logo && result.logo.startsWith('http')) {
      result.logo = null;
    }
    if (result.black_white_logo && result.black_white_logo.startsWith('http')) {
      result.black_white_logo = null;
    }
    this.save.emit(result);
  }
}
