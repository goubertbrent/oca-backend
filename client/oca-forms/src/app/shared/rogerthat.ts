export interface ServiceMenuItemLink {
  url: string;
  external: boolean;
}

export interface FormVersion {
  id: number;
  version: number;
}

export interface ServiceMenuDetailItem {
  tag: string;
  coords: [ number, number, number ];
  label: string;
  iconHash: string;
  screenBranding: string | null;
  staticFlowHash: string | null;
  requiresWifi: boolean;
  runInBackground: boolean;
  action: number;
  roles: number[];
  link: ServiceMenuItemLink | null;
  fallThrough: boolean;
  form: FormVersion | null;
}

export interface ServiceMenuDetail {
  aboutLabel: string;
  callConfirmation: string | null;
  callLabel: string | null;
  items: ServiceMenuDetailItem[];
  messageLabel: string;
  shareLabel: string;
}
