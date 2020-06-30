import { NewsSenderTO, NewsStreamItemTO } from 'rogerthat-plugin';

export type UserData = Readonly<{ [ key: string ]: any }>;
export type ServiceData = Readonly<{ [ key: string ]: any }>;

export interface AppVersion {
  major: number;
  minor: number;
  patch: number;
}

export interface NewsSender extends NewsSenderTO {
  avatar_url: string;
}

export interface NewsStreamItem extends NewsStreamItemTO {
  sender: NewsSender;
  date: Date;
}
