import { GetNewsStreamFilterTO } from '@oca/web-shared';

export interface TranslationInternal {
  key: string;
  value: string;
  prefixedKey: string;
}

export interface TranslationValue {
  [ key: string ]: string;
}


export const enum HomeScreenSectionType {
  TEXT = 'text',
  LIST = 'list',
  NEWS = 'news',
}

export const enum BottomSheetListItemType {
  OPENING_HOURS = 'opening-hours',
  EXPANDABLE = 'expandable',
  LINK = 'link',
}

export const enum ListSectionStyle {
  HORIZONTAL = 'horizontal',
  VERTICAL = 'vertical',
}

export const enum ExpandableItemSource {
  NONE,
  SERVICE_INFO_DESCRIPTION,
}

export const enum LinkItemSource {
  NONE,
  SERVICE_INFO_PHONE,
  SERVICE_INFO_EMAIL,
  SERVICE_INFO_WEBSITE,
  SERVICE_INFO_ADDRESS,
  SERVICE_MENU_ITEM,
}

export const enum LinkListItemStyle {
  ROUND_BUTTON_WITH_ICON,
  BUTTON,
}

export interface OpeningHoursItemTemplate {
  type: BottomSheetListItemType.OPENING_HOURS;
}

export interface ExpandableItemTemplate {
  type: BottomSheetListItemType.EXPANDABLE;
  source: ExpandableItemSource;
  icon: string | null;
  title: string | null;
}

export interface LinkItemContentDefault {
  source: LinkItemSource.NONE;
  url: string;
  external: boolean;
  request_user_link: boolean;
}

export interface LinkItemSyncedContent {
  source: LinkItemSource.SERVICE_INFO_EMAIL | LinkItemSource.SERVICE_INFO_PHONE | LinkItemSource.SERVICE_INFO_WEBSITE;
  index: number;
}

export interface LinkItemAddress {
  source: LinkItemSource.SERVICE_INFO_ADDRESS;
}

export interface LinkItemServiceMenuItem {
  source: LinkItemSource.SERVICE_MENU_ITEM;
  service: string;
  tag: string;
}

export type LinkItemContent = LinkItemContentDefault | LinkItemSyncedContent | LinkItemAddress | LinkItemServiceMenuItem;

export interface LinkItemTemplate {
  type: BottomSheetListItemType.LINK;
  content: LinkItemContent;
  title: string | null;
  icon: string | null;
  icon_color: string | null;
  style: LinkListItemStyle;
}

export type BottomSheetListItemTemplate = OpeningHoursItemTemplate | ExpandableItemTemplate | LinkItemTemplate;

export interface TextSectionTemplate {
  type: HomeScreenSectionType.TEXT;
  title: string;
  description: string | null;
}

export interface ListSectionTemplate {
  type: HomeScreenSectionType.LIST;
  style: ListSectionStyle;
  items: BottomSheetListItemTemplate[];
}

export interface NewsSectionTemplate {
  type: HomeScreenSectionType.NEWS;
  filter: GetNewsStreamFilterTO;
  limit: number;
}

export type BottomSheetSectionTemplate = TextSectionTemplate | ListSectionTemplate | NewsSectionTemplate;

export interface HomeScreenDefaultTranslation {
  key: string;
  values: {
    [ key: string ]: string;
  };
}
