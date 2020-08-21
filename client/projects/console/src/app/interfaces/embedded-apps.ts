import { AppTypes } from './apps.interfaces';

export const enum EmbeddedAppTag {
  PAYMENTS = 'payments'
}

export const enum EmbeddedAppType {
  CHAT_PAYMENT = 'chat-payment',
  WIDGET_PAY = 'widget-pay',
}

export interface EmbeddedApp {
  name: string;
  tags: EmbeddedAppTag[];
  modification_date: string;
  serving_url: string;
  url_regexes: string[];
  title: string | null;
  types: EmbeddedAppType[];
  description: string | null;
  app_types: AppTypes[];
}

export const EMBEDDED_APP_TAGS = [
  { label: 'rcc.payments', value: EmbeddedAppTag.PAYMENTS },
];

export const EMBEDDED_APP_TYPES = [
  { label: 'rcc.chat_payment', value: EmbeddedAppType.CHAT_PAYMENT },
  { label: 'rcc.pay_widget', value: EmbeddedAppType.WIDGET_PAY },
];

export interface SaveEmbeddedApp {
  tags: EmbeddedAppTag[];
  name: string;
  file: string | null;
  url_regexes: string[];
  title: string | null;
  types: EmbeddedAppType[];
  description: string | null;
  app_types: AppTypes[];
}
