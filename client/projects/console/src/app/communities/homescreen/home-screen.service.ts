import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { FormBuilder, Validators } from '@angular/forms';
import { GetNewsStreamFilterTO } from '@oca/web-shared';
import { IFormBuilder, IFormGroup } from '@rxweb/types';
import { SERVICE_IDENTITY_REGEX } from '../../constants';
import {
  BottomSheetListItemTemplate,
  BottomSheetListItemType,
  BottomSheetSectionTemplate,
  ExpandableItemTemplate,
  HomeScreenDefaultTranslation,
  HomeScreenSectionType,
  LinkItemAddress,
  LinkItemContent,
  LinkItemContentDefault,
  LinkItemServiceMenuItem,
  LinkItemSource,
  LinkItemSyncedContent,
  LinkItemTemplate,
  ListSectionTemplate,
  NewsSectionTemplate,
  OpeningHoursItemTemplate,
  TextSectionTemplate,
} from './homescreen';

@Injectable({ providedIn: 'root' })
export class HomeScreenService {
  private formBuilder: IFormBuilder;

  constructor(formBuilder: FormBuilder,
              private http: HttpClient) {
    this.formBuilder = formBuilder;

  }

  getDefaultTranslations() {
    return this.http.get<HomeScreenDefaultTranslation[]>('/console-api/home-screen-translations');
  }

  getHomeScreenItemForm(item: BottomSheetSectionTemplate): IFormGroup<BottomSheetSectionTemplate> {
    switch (item.type) {
      case HomeScreenSectionType.TEXT:
        return this.formBuilder.group<TextSectionTemplate>(
          {
            type: this.formBuilder.control(item.type, Validators.required),
            title: this.formBuilder.control(item.title, Validators.required),
            description: this.formBuilder.control(item.description),
          },
        );
      case HomeScreenSectionType.LIST:
        return this.formBuilder.group<ListSectionTemplate>({
          type: this.formBuilder.control(item.type, Validators.required),
          style: this.formBuilder.control(item.style, Validators.required),
          items: this.formBuilder.array(item.items.map(listItem => this.getListItemForm(listItem)), Validators.required),
        });
      case HomeScreenSectionType.NEWS:
        return this.formBuilder.group<NewsSectionTemplate>({
          type: this.formBuilder.control(item.type, Validators.required),
          limit: this.formBuilder.control(item.limit, Validators.required),
          filter: this.formBuilder.group <GetNewsStreamFilterTO>({
            group_id: this.formBuilder.control(item.filter.group_id),
            group_type: this.formBuilder.control(item.filter.group_type),
            search_string: this.formBuilder.control(item.filter.search_string),
            service_identity_email: this.formBuilder.control(item.filter.service_identity_email,
              Validators.pattern(SERVICE_IDENTITY_REGEX)),
          }),
        });
    }
  }

  getListItemForm(item: BottomSheetListItemTemplate): IFormGroup<BottomSheetListItemTemplate> {
    switch (item.type) {
      case BottomSheetListItemType.OPENING_HOURS:
        return this.formBuilder.group<OpeningHoursItemTemplate>({
          type: this.formBuilder.control(item.type, Validators.required),
        });
      case BottomSheetListItemType.EXPANDABLE:
        return this.formBuilder.group<ExpandableItemTemplate>({
          type: this.formBuilder.control(item.type, Validators.required),
          source: this.formBuilder.control(item.source, Validators.required),
          icon: this.formBuilder.control(item.icon),
          title: this.formBuilder.control(item.title),
        });
      case BottomSheetListItemType.LINK:
        return this.formBuilder.group<LinkItemTemplate>({
          type: this.formBuilder.control(item.type, Validators.required),
          icon: this.formBuilder.control(item.icon),
          icon_color: this.formBuilder.control(item.icon_color),
          style: this.formBuilder.control(item.style, Validators.required),
          title: this.formBuilder.control(item.title),
          content: this.getLinkItemContentForm(item.content),
        });
    }
  }

  getLinkItemContentForm(item: LinkItemContent): IFormGroup<LinkItemContent> {
    switch (item.source) {
      case LinkItemSource.NONE:
        return this.formBuilder.group<LinkItemContentDefault>({
          source: this.formBuilder.control(item.source, Validators.required),
          url: this.formBuilder.control(item.url, Validators.required),
          external: this.formBuilder.control(item.external),
          request_user_link: this.formBuilder.control(item.request_user_link),
        });
      case LinkItemSource.SERVICE_INFO_EMAIL:
      case LinkItemSource.SERVICE_INFO_PHONE:
      case LinkItemSource.SERVICE_INFO_WEBSITE:
        return this.formBuilder.group<LinkItemSyncedContent>({
          source: this.formBuilder.control(item.source, Validators.required),
          index: this.formBuilder.control(item.index, Validators.required),
        });
      case LinkItemSource.SERVICE_INFO_ADDRESS:
        return this.formBuilder.group<LinkItemAddress>({
          source: this.formBuilder.control(item.source, Validators.required),
        });
      case LinkItemSource.SERVICE_MENU_ITEM:
        return this.formBuilder.group<LinkItemServiceMenuItem>({
          source: this.formBuilder.control(item.source, Validators.required),
          service: this.formBuilder.control(item.service, Validators.required),
          tag: this.formBuilder.control(item.tag, Validators.required),
        });
    }
  }
}
