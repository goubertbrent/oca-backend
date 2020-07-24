import { HttpClient } from '@angular/common/http';
import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  ElementRef,
  forwardRef,
  Input,
  OnChanges,
  SimpleChanges,
  ViewChild,
  ViewEncapsulation,
} from '@angular/core';
import { ControlValueAccessor, NG_VALUE_ACCESSOR } from '@angular/forms';
import { TranslateService } from '@ngx-translate/core';
import { App, AppStatisticsMapping } from '@oca/web-shared';
import { getCost, getReach } from '../../utils';

interface CountryMapData {
  width: number;
  height: number;
  cities: {
    [ key: string ]: string;
  };
}

interface MapaelArea {
  tooltip?: {
    content: string | HTMLElement;
  };
  value: string;
  attrs: {
    fill: string;
    cursor: 'pointer' | 'default';
  };
  eventHandlers: {
    click?: (event: Event, id: string, mapElem: HTMLElement, textElem: HTMLElement, elementOptions: any) => void;
  };
}

const enum AreaValue {
  /**
   *  We have no app for this city
   */
  DEFAULT = 'default',
  /**
   * Value for the default app
   */
  DEFAULT_APP = 'defaultApp',
  /**
   * We have an app for this city, user has selected it
   */
  SELECTED = 'selected',
  /**
   * We have an app for this city, user hasn't selected it
   */
  UNSELECTED = 'unselected',
}

@Component({
  selector: 'oca-news-app-map-picker',
  templateUrl: './news-app-map-picker.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
  providers: [{
    provide: NG_VALUE_ACCESSOR,
    useExisting: forwardRef(() => NewsAppMapPickerComponent),
    multi: true,
  }],
})
export class NewsAppMapPickerComponent implements ControlValueAccessor, OnChanges {
  @ViewChild('mapContainer', { static: true }) mapContainer: ElementRef<HTMLDivElement>;
  @Input() readonly: boolean;
  @Input() showLegend: boolean;
  @Input() apps: App[];
  @Input() defaultAppId: string;
  @Input() appStatistics: AppStatisticsMapping;
  @Input() mapUrl: string;
  private colors = {
    [ AreaValue.DEFAULT ]: '#ffffff',
    [ AreaValue.DEFAULT_APP ]: '#6a8acd',
    [ AreaValue.SELECTED ]: '#5bc4bF',
    [ AreaValue.UNSELECTED ]: '#f4f4e9',
    hover: '#a3e135',
    stroke: '#ced8d0',
    text: '#000000',

  };
  private appNameMapping: { [ key: string ]: string; }; // key: app name, value: app id
  private $: typeof jQuery | null;
  private initializedMapUrl: string;

  constructor(private changeDetectorRef: ChangeDetectorRef,
              private translate: TranslateService,
              private http: HttpClient) {
  }

  private _appIds: string[];

  get appIds(): string[] {
    return this._appIds;
  }

  set appIds(values: string[]) {
    // Don't set 'changed' in case of initial value
    if (this._appIds) {
      this.onChange(values);
    }
    this._appIds = values;
  }

  ngOnChanges(changes: SimpleChanges): void {
    // Needs both apps and appStatistics before we can render
    const hasRelevantChanges = changes.apps || changes.appStatistics || changes.mapUrl;
    if (hasRelevantChanges && (this.apps && this.apps.length && Object.keys(this.appStatistics).length > 0) && this.mapUrl) {
      this.appNameMapping = {};
      for (const app of this.apps) {
        this.appNameMapping[ app.name ] = app.id;
      }
      if (this.initializedMapUrl !== this.mapUrl) {
        this.http.get<CountryMapData>(this.mapUrl).subscribe(async data => await this.initializeMap(data));
        this.initializedMapUrl = this.mapUrl;
      }
    }
  }

  registerOnChange(fn: any): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: any): void {
    this.onTouched = fn;
  }

  setDisabledState(isDisabled: boolean): void {
  }

  writeValue(values?: string[]): void {
    if (values) {
      this._appIds = values;
      if (this.$) {
        this.setAreas();
      }
      this.changeDetectorRef.markForCheck();
    }
  }

  private onChange = (_: any) => {
  };

  private onTouched = () => {
  };

  private getTooltip(city: string) {
    const appId = this.appNameMapping[ city ];
    if (appId && !this.readonly) {
      const stats = this.appStatistics[ appId ] || { total_user_count: 0, app_id: appId };
      const userCount = stats.total_user_count;
      const costCount = appId === this.defaultAppId ? 0 : userCount;
      const estimatedReach = getReach(userCount);
      const costReach = getReach(costCount);
      const estimatedCost = getCost('€', costReach.lowerGuess, costReach.higherGuess);
      return `<b>${city}</b><br>
${this.translate.instant('oca.broadcast-estimated-reach')}: ${estimatedReach.lowerGuess} - ${estimatedReach.higherGuess}
<br>${this.translate.instant('oca.broadcast-estimated-cost')} ${estimatedCost}`;
    } else {
      return city;
    }
  }

  private toggleArea(areaName: string) {
    const appId = this.appNameMapping[ areaName ];
    const canSelect = areaName in this.appNameMapping;
    const appSelected = canSelect && !this.appIds.includes(appId);
    if (appSelected) {
      this.appIds = [...this.appIds, appId];
    } else {
      this.appIds = this.appIds.filter(a => a !== appId);
    }
    this.setAreas();
  }

  private setAreas() {
    const areas: { [ key: string ]: Partial<MapaelArea> } = {};
    for (const areaName of Object.keys(this.appNameMapping)) {
      const appId = this.appNameMapping[ areaName ];
      const areaValue = this.getAreaValue(areaName, this.appIds.includes(appId));
      areas[ areaName ] = {
        value: areaValue,
        attrs: {
          fill: this.colors[ areaValue ],
          cursor: areaValue === AreaValue.DEFAULT ? 'default' : 'pointer',
        },
      };
    }
    // Update the map
    if (this.$) {
      this.$(this.mapContainer.nativeElement).trigger('update', [{
        mapOptions: {
          areas,
        },
      }]);
    }
  }

  private getAreaValue(areaName: string, selected: boolean): AreaValue {
    const appId = this.appNameMapping[ areaName ];
    if (selected) {
      if (appId === this.defaultAppId) {
        return AreaValue.DEFAULT_APP;
      }
      return AreaValue.SELECTED;
    }
    if (areaName in this.appNameMapping) {
      return AreaValue.UNSELECTED;
    }
    return AreaValue.DEFAULT;
  }


  private async initializeMap(mapData: CountryMapData) {
    const [jq, _] = await Promise.all([import('jquery'), import('jquery-mapael')]);
    const $ = (jq as any).default as typeof jQuery;
    this.$ = $;
    const areas: { [ key: string ]: MapaelArea } = {};
    for (const areaName of Object.keys(mapData.cities)) {
      const appId = this.appNameMapping[ areaName ];
      const value = this.getAreaValue(areaName, this.appIds.includes(appId));
      const area: MapaelArea = {
        value,
        attrs: {
          fill: this.colors[ value ],
          cursor: value === AreaValue.DEFAULT ? 'default' : 'pointer',
        },
        eventHandlers: {
          click: (event, id, mapElem, textElem, elementOptions) => {
            if (!this.readonly) {
              this.toggleArea(id);
            }
          },
        },
      };
      area.tooltip = { content: this.getTooltip(areaName) };
      areas[ areaName ] = area;
    }
    const options = {
      map: {
        name: 'cities',
        defaultArea: {
          value: AreaValue.DEFAULT,
          attrs: {
            fill: this.colors.default,
            stroke: this.colors.stroke,
          },
          attrsHover: {
            animDuration: 0,
            fill: this.readonly ? this.colors.unselected : this.colors.hover,
          },
          text: {
            attrs: {
              cursor: 'pointer',
              'font-size': 10,
              fill: this.colors.text,
            },
            attrsHover: {
              animDuration: 0,
            },
          },
        },
      },
      areas,
    } as any;
    if (this.showLegend) {
      options.legend = {
        area: {
          title: '',
          slices: [
            {
              sliceValue: AreaValue.DEFAULT_APP,
              label: this.translate.instant('oca.city_select_default_city'),
              attrs: { fill: this.colors.defaultApp },
            },
            {
              sliceValue: AreaValue.DEFAULT,
              label: this.translate.instant('oca.city_select_unsupported'),
              attrs: { fill: this.colors.default },
            },
            {
              sliceValue: AreaValue.SELECTED,
              label: this.translate.instant('oca.city_select_selected'),
              attrs: { fill: this.colors.selected },
            },
            {
              sliceValue: AreaValue.UNSELECTED,
              label: this.translate.instant('oca.city_select_unselected'),
              attrs: { fill: this.colors.unselected },
            },
          ],
        },
      };
    }
    ($ as any).mapael.maps = {
      ...($ as any).mapael.maps, cities: {
        width: mapData.width,
        height: mapData.height,
        getCoords: (lat: number, lon: number) => ({ x: 1, y: 1 }),
        elems: mapData.cities,
      },
    };
    ($(this.mapContainer.nativeElement) as any).mapael(options);
  }
}
