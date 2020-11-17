import { ChangeDetectionStrategy, ChangeDetectorRef, Component, forwardRef, OnDestroy } from '@angular/core';
import { ControlValueAccessor, FormBuilder, FormGroup, NG_VALUE_ACCESSOR, ValidatorFn, Validators } from '@angular/forms';
import { IFormBuilder, IFormControl, IFormGroup } from '@rxweb/types';
import { merge, Subject } from 'rxjs';
import { debounceTime, filter, takeUntil } from 'rxjs/operators';

export enum AppActionType {
  WEBSITE = 'https://',
  PHONE = 'tel://',
  EMAIL = 'mailto://',
  OPEN = 'open://',
}

export enum OpenActionType {
  OPEN_SERVICE_FUNCTION = 'click',
  EMBEDDED_APP = 'embedded-app',
  MAP = 'map',
  JOB = 'job',
  OPEN_EXTERNAL_APPLICATION = 'open',
}

interface AppFunctionParam {
  inputType: 'text' | 'number' | 'email';
  key: string;
  label: string;
  required?: boolean;
}

interface AppFunction {
  action: string;
  params: AppFunctionParam[];
  label: string;
}

interface OpenForm {
  action: string | null;
  action_type: string | null;

  [ key: string ]: string | number | null;
}

interface OpenActionItem {
  actionType: string | null;
  label: string;
  params: AppFunctionParam[];
}

@Component({
  selector: 'rcc-app-action-editor',
  templateUrl: './app-action-editor.component.html',
  styleUrls: ['./app-action-editor.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
  providers: [{
    provide: NG_VALUE_ACCESSOR,
    useExisting: forwardRef(() => AppActionEditorComponent),
    multi: true,
  }],
})
export class AppActionEditorComponent implements OnDestroy, ControlValueAccessor {
  AppActionType = AppActionType;
  types = [
    { value: AppActionType.WEBSITE, label: 'Website' },
    { value: AppActionType.PHONE, label: 'Phone number' },
    { value: AppActionType.EMAIL, label: 'Email address' },
    { value: AppActionType.OPEN, label: 'Open app function' },
  ];
  mapTypes = [
    { tag: 'gipod', label: 'Gipod' },
    { tag: 'services', label: 'Services' },
    { tag: 'reports', label: 'Reports' },
  ];
  OpenAction = OpenActionType;
  openActionTypes: OpenActionItem[] = [
    { actionType: null, label: 'App function', params: [] },
    {
      actionType: OpenActionType.OPEN_SERVICE_FUNCTION, label: 'Service function', params: [
        { key: 'service', inputType: 'email', label: 'Service email', required: true },
      ],
    },
    {
      actionType: OpenActionType.EMBEDDED_APP, label: 'Embedded app', params: [
        { key: 'service', inputType: 'email', label: 'Service email', required: false },
      ],
    },
    { actionType: OpenActionType.MAP, label: 'Map', params: [] },
    { actionType: OpenActionType.JOB, label: 'Job', params: [] },
    { actionType: OpenActionType.OPEN_EXTERNAL_APPLICATION, label: 'External application', params: [
        {key: 'android_app_id', inputType: 'text', label: 'Android app id', required: true},
        {key: 'android_scheme', inputType: 'text', label: 'Android scheme', required: true},
        {key: 'ios_app_id', inputType: 'text', label: 'iOS app id', required: true},
        {key: 'ios_scheme', inputType: 'text', label: 'iOS scheme', required: true},
      ] },
  ];
  appFunctions: AppFunction[] = [
    { action: 'home', label: 'Home', params: [] },
    {
      action: 'news', label: 'News', params: [
        { key: 'group_id', inputType: 'text', label: 'Group id' },
        { key: 'filter', inputType: 'text', label: 'Filter' },
        { key: 'service', inputType: 'email', label: 'Service (email)' },
        { key: 'name', inputType: 'text', label: 'Group name' },
        { key: 'id', inputType: 'number', label: 'News id' },
      ],
    },
    {
      action: 'news_stream_group', label: 'News stream', params: [
        { key: 'id', inputType: 'number', label: 'News id' },
        { key: 'service', inputType: 'email', label: 'Service (email)' },
        { key: 'group_id', inputType: 'text', label: 'Group id' },
      ],
    },
    { action: 'messages', label: 'Messages', params: [] },
    { action: 'scan', label: 'Scan', params: [] },
    { action: 'friends', label: 'Friends', params: [] },
    { action: 'profile', label: 'Profile', params: [] },
    { action: 'more', label: 'More', params: [] },
    { action: 'settings', label: 'Settings', params: [] },
    { action: 'jobs', label: 'Jobs', params: [] },
    { action: 'services', label: 'Services', params: [] },
    { action: 'community_services', label: 'Community services', params: [] },
    { action: 'merchants', label: 'Merchants', params: [] },
    { action: 'associations', label: 'Associations', params: [] },
    { action: 'emergency_services', label: 'Emergency services', params: [] },
    { action: 'qrcode', label: 'Qr code', params: [] },
  ];

  appActionTypeControl: IFormControl<string | null>;
  websiteFormGroup: IFormGroup<{ url: string }>;
  phoneFormGroup: IFormGroup<{ phone: string }>;
  emailFormGroup: IFormGroup<{ email: string }>;
  openFormGroup: IFormGroup<OpenForm>;
  appFunctionParams$ = new Subject<AppFunctionParam[]>();

  private destroyed$ = new Subject();
  private formBuilder: IFormBuilder;
  private value: string | null = null;
  private onChange: (_: any) => void;
  private onTouched: () => void;
  private URL_PATTERN = '(https?:\\/\\/)?([\\w\\-])+\\.{1}([a-zA-Z]{2,63})([\\/\\w-]*)*\\/?\\??([^#\\n\\r]*)?#?([^\\n\\r]*)';


  constructor(formBuilder: FormBuilder,
              private changeDetectorRef: ChangeDetectorRef) {
    this.formBuilder = formBuilder;
    this.appActionTypeControl = this.formBuilder.control(null, Validators.required);
    this.websiteFormGroup = this.formBuilder.group<{ url: string }>({
      url: this.formBuilder.control('', [Validators.required, Validators.pattern(this.URL_PATTERN)]),
    });
    this.phoneFormGroup = this.formBuilder.group<{ phone: string }>({
      phone: this.formBuilder.control('', Validators.required),
    });
    this.emailFormGroup = this.formBuilder.group<{ email: string }>({
      email: this.formBuilder.control('', [Validators.required, Validators.email]),
    });
    this.openFormGroup = this.formBuilder.group<OpenForm>({
      action: this.formBuilder.control(null),
      action_type: this.formBuilder.control(null),
    });
    this.phoneFormGroup.statusChanges.pipe(filter(status => status === 'VALID'), takeUntil(this.destroyed$)).subscribe(() => {
      this.setValue(AppActionType.PHONE + this.phoneFormGroup.value!.phone);
    });
    this.emailFormGroup.statusChanges.pipe(filter(status => status === 'VALID'), takeUntil(this.destroyed$)).subscribe(() => {
      this.setValue(AppActionType.EMAIL + this.emailFormGroup.value!.email);
    });
    this.websiteFormGroup.statusChanges.pipe(filter(status => status === 'VALID'), takeUntil(this.destroyed$)).subscribe(() => {
      const value = this.websiteFormGroup.value!.url;
      this.setValue(value.startsWith('http://') || value.startsWith('https://') ? value : `https://${value}`);
    });
    // when action or action type changes, ensure the correct fields are shown.
    merge(this.openFormGroup.controls.action.valueChanges, this.openFormGroup.controls.action_type.valueChanges).pipe(
      // Wait for changes to propagate so that both action and action_type are set
      debounceTime(10),
      takeUntil(this.destroyed$)).subscribe(() => {
      const { action, action_type } = this.openFormGroup.value!!;
      this.setOpenFormControls(action_type, action);
    });
    this.openFormGroup.valueChanges.pipe(takeUntil(this.destroyed$)).subscribe(form => {
      if (this.openFormGroup.valid && form) {
        // Remove keys with null value (except for action_type)
        const result = Object.fromEntries(Object.entries(form).filter(([key, value]) => key === 'action_type' || value !== null));
        this.setValue(AppActionType.OPEN + JSON.stringify(result, Object.keys(result).sort()));
      }
    });
  }

  setValue(value: string) {
    if (this.onChange && value !== this.value) {
      this.value = value;
      this.onChange(this.value);
    }
  }

  ngOnDestroy() {
    this.destroyed$.next();
    this.destroyed$.complete();
  }

  writeValue(value: string) {
    this.value = value;
    this.setFormsFromValue(value);
    this.changeDetectorRef.markForCheck();
  }

  registerOnChange(fn: (value: string) => void): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: () => void): void {
    this.onTouched = fn;
  }

  setDisabledState(isDisabled: boolean): void {
    if (isDisabled) {
      this.appActionTypeControl.disable();
      this.websiteFormGroup.disable();
      this.emailFormGroup.disable();
      this.phoneFormGroup.disable();
      this.openFormGroup.disable();
    } else {
      this.appActionTypeControl.enable();
      this.websiteFormGroup.enable();
      this.emailFormGroup.enable();
      this.phoneFormGroup.enable();
      this.openFormGroup.enable();
    }
  }

  private setFormsFromValue(value: string) {
    const prefix = [AppActionType.WEBSITE, AppActionType.EMAIL, AppActionType.PHONE, AppActionType.OPEN].find(v => value.startsWith(v));
    if (!prefix) {
      return;
    }
    const valueWithoutPrefix = value.replace(prefix, '');
    this.appActionTypeControl.setValue(prefix);
    switch (prefix) {
      case AppActionType.WEBSITE:
        this.websiteFormGroup.setValue({ url: valueWithoutPrefix });
        break;
      case AppActionType.EMAIL:
        this.emailFormGroup.setValue({ email: valueWithoutPrefix });
        break;
      case AppActionType.PHONE:
        this.phoneFormGroup.setValue({ phone: valueWithoutPrefix });
        break;
      case AppActionType.OPEN:
        const parsed = JSON.parse(valueWithoutPrefix);
        this.setOpenFormControls(parsed.actionType, parsed.action);
        this.openFormGroup.patchValue(parsed);
        break;
    }
  }

  private setOpenFormControls(actionType: string | null, action: string | null) {
    let params: AppFunctionParam[];
    if (actionType === null) {
      params = this.appFunctions.find(f => f.action === action)?.params ?? [];
    } else {
      params = this.openActionTypes.find(f => f.actionType === actionType)?.params ?? [];
    }
    this.appFunctionParams$.next(params);
    this.setControls(this.openFormGroup, params);
    // Force change detection as we need the form controls to be created in the template before setting the value
    this.changeDetectorRef.detectChanges();
  }

  private setControls(formGroup: FormGroup, params: AppFunctionParam[]) {
    const currentControls = Object.keys(formGroup.controls);
    const neededParams = params.map(p => p.key);
    for (const control of currentControls) {
      if (control === 'action' || control === 'action_type' || neededParams.includes(control)) {
        continue;
      }
      formGroup.removeControl(control);
    }
    for (const param of params) {
      if (currentControls.includes(param.key)) {
        continue;
      }
      const validators: ValidatorFn[] = [];
      if (param.inputType === 'email') {
        validators.push(Validators.email);
      }
      formGroup.addControl(param.key, this.formBuilder.control(null, validators));
    }
  }
}
