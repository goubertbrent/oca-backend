import {ChangeDetectionStrategy, Component, OnInit} from '@angular/core';
import {SelectedMarker} from "../../marker.model";
import {select, Store} from '@ngrx/store';
import {Observable} from "rxjs";
import {getSelectedMarker} from '../../map.selectors'
import {MapItemLineTextPartTO, MapSectionType, OpeningHoursTO, OpeningInfoTO} from "@oca/web-shared";
import {MapListSectionItemType} from "../../../../../../web-shared/src/lib/types";

@Component({
  selector: 'app-marker-detail',
  templateUrl: './marker-detail.component.html',
  styleUrls: ['./marker-detail.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MarkerDetailComponent implements OnInit {
  marker$: Observable<SelectedMarker | null>;

  SECTION_TYPE_LIST = MapSectionType.LIST
  SECTION_TYPE_NEWS_GROUP = MapSectionType.NEWS_GROUP
  SECTION_TYPE_GEOMETRY = MapSectionType.GEOMETRY
  SECTION_TYPE_MEDIA = MapSectionType.MEDIA
  SECTION_TYPE_TEXT = MapSectionType.TEXT
  SECTION_TYPE_VOTE = MapSectionType.VOTE
  SECTION_TYPE_NEWS = MapSectionType.NEWS


  MAP_LIST_ITEM_TYPE_LINK = MapListSectionItemType.LINK;
  MAP_LIST_ITEM_TYPE_EXPANDABLE = MapListSectionItemType.EXPANDABLE;
  MAP_LIST_ITEM_TYPE_DYNAMIC_OPENING_HOURS = MapListSectionItemType.DYNAMIC_OPENING_HOURS;
  MAP_LIST_ITEM_TYPE_OPENING_HOURS = MapListSectionItemType.OPENING_HOURS;
  MAP_LIST_ITEM_TYPE_TOGGLE = MapListSectionItemType.TOGGLE;

  HORIZONTAL= 'horizontal';

  constructor(private store: Store) { }

  ngOnInit(): void {
     this.marker$ = this.store.pipe(select(getSelectedMarker));
  }

  isOpen(opening_hours: OpeningHoursTO) : string {
    let OPEN = 'Geopend'
    let CLOSED = 'Gesloten'

    let currentDate: Date = new Date()
    let currentDay = currentDate.getDay()
    let currentHourMinutes = currentDate.getHours() *100 + currentDate.getMinutes()

    let openHour : string = "";
    let closingHour : string = "";

    for(let period of opening_hours.periods) {
      if(currentDay == period.close?.day){
        if(period.open?.time != null)
        {
          openHour = period.open?.time;
        }

        if(period.close?.time != null)
        {
          closingHour = period.close?.time;
        }
        break;
      }
    }

    if(openHour == "" || closingHour == "")
    {
      return CLOSED;
    }
    else if(Number(openHour) > currentHourMinutes || Number(closingHour) < currentHourMinutes)
    {
      return CLOSED;
    }

    return OPEN;
  }


}
