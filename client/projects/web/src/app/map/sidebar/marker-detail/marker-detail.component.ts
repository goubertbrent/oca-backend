import {ChangeDetectionStrategy, Component, OnInit} from '@angular/core';
import {SelectedMarker} from "../../marker.model";
import {select, Store} from '@ngrx/store';
import {Observable} from "rxjs";
import {getSelectedMarker} from '../../map.selectors'
import {MapSectionType, OpeningHourExceptionTO, OpeningHoursTO, OpeningPeriodTO} from "@oca/web-shared";
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
  SECTION_TYPE_MEDIA = MapSectionType.MEDIA
  // SECTION_TYPE_TEXT = MapSectionType.TEXT
  // SECTION_TYPE_NEWS = MapSectionType.NEWS
  // SECTION_TYPE_NEWS_GROUP = MapSectionType.NEWS_GROUP


  MAP_LIST_ITEM_TYPE_LINK = MapListSectionItemType.LINK;
  MAP_LIST_ITEM_TYPE_EXPANDABLE = MapListSectionItemType.EXPANDABLE;
  MAP_LIST_ITEM_TYPE_DYNAMIC_OPENING_HOURS = MapListSectionItemType.DYNAMIC_OPENING_HOURS;

  MEDIA_TYPE_IMAGE = 'image';
  MEDIA_TYPE_VIDEO = 'video_youtube';

  HORIZONTAL = 'horizontal';


  constructor(private store: Store) {
  }

  ngOnInit(): void {
    this.marker$ = this.store.pipe(select(getSelectedMarker));
  }

  isOpen(opening_hours: OpeningHoursTO, timezone: string): string {
    let periods = opening_hours.periods;
    let currentDate = new Date();
    let test = currentDate.getTimezoneOffset()
    console.log(test)
    console.log(timezone);

    let exceptionOpenOrClosed = this.checkExceptionalHours(opening_hours.exceptional_opening_hours, currentDate);
    if (exceptionOpenOrClosed != '') //if date is in period of exceptional hours
    {
      return exceptionOpenOrClosed;
    }

    if (this.isAlwaysOpen(periods)) {
      return 'Open 24/7';
    }

    if (periods.length == 0) {
      return 'Altijd gesloten';
    }

    return this.getOpenOrClosedString(periods, currentDate);
  }

  showOpening(period: OpeningPeriodTO): string {
    let day = ''
    let openHour = ''
    let closeHour = ''
    if (period.open) {
      day = this.WeekdayNumberToString(period.open?.day)
    }
    if (!period.close) {
      return `${day}: Hele dag open`
    }

    if (period.open?.time) {
      openHour = this.formatHourToDisplayStyle(period.open.time);
    }

    if (period.close.time) {
      closeHour = this.formatHourToDisplayStyle(period.close.time);
    }

    return `${day}: ${openHour}-${closeHour}`
  }

  private WeekdayNumberToString(day: number): string {
    switch (day) {
      case 0:
        return 'zondag';
      case 1:
        return 'maandag';
      case 2:
        return 'dinsdag';
      case 3:
        return 'woensdag';
      case 4:
        return 'donderdag';
      case 5:
        return 'vrijdag';
      case 6:
        return 'zaterdag';
      default:
        return '';
    }
    ;
  }


  private checkExceptionalHours(exceptional_opening_hours: OpeningHourExceptionTO[], currentDate: Date): string {
    if (exceptional_opening_hours != []) {
      for (let openingHourException of exceptional_opening_hours) {

        let startDate = this.dateStringToNumber(openingHourException.start_date);
        let endDate = this.dateStringToNumber(openingHourException.end_date);
        let today = currentDate.getFullYear() * 10000 + (currentDate.getMonth() + 1) * 100 + currentDate.getDay()
        if (startDate <= today && endDate >= today) {
          return this.getOpenOrClosedString(openingHourException.periods, currentDate);
        }
      }
    }
    return '';
  }

  private getOpenOrClosedString(periods: OpeningPeriodTO[], currentDate: Date): string {
    let currentDay = currentDate.getDay();
    let currentHourMinutes = currentDate.getHours() * 100 + currentDate.getMinutes();
    let openHour = ''
    let closingHour = ''

    for (let period of periods) {
      if (currentDay == period.open?.day) {

        if (this.isOpenEntireDay(period)) {
          return 'Hele dag open';
        }

        if (period.open?.time != null) {
          openHour = period.open?.time;
        }
        if (period.close?.time != null) {
          closingHour = period.close?.time;
        }

        if (Number(openHour) <= currentHourMinutes && Number(closingHour) > currentHourMinutes) {
          return `Geopend tot ${this.formatHourToDisplayStyle(closingHour)}`
        }
        if (Number(openHour) > currentHourMinutes) {
          return `Gesloten -  Open om ${this.formatHourToDisplayStyle(openHour)}`
        }

      }
    }
    return 'Gesloten'
  }

  private dateStringToNumber(dateString: string | null) {

    let output = '';
    if (dateString != null) {
      let startYear: string = dateString.substring(0, 4)
      let startMonth: string = dateString.substring(5, 7)
      let startDay: string = dateString.substring(8, 10)
      output = startYear + startMonth + startDay
    }
    return Number(output);
  }

  private isAlwaysOpen(periods: OpeningPeriodTO[]): boolean {
    return periods.length == 7 && this.isOpen24Hours(periods)
  }

  private isOpen24Hours(periods: OpeningPeriodTO[]): boolean {
    for (let period of periods) {
      if (!this.isOpenEntireDay(period) || period.open?.time != '0000') {
        return false;
      }
    }

    return true;
  }

  private isOpenEntireDay(period: OpeningPeriodTO) {
    return period.close == null;
  }

  private formatHourToDisplayStyle(time: string): string {
    return `${time.substring(0,2)}:${time.substring(2,4)}`;
  }

  convertUrl(url: string) {
    
  }
}
