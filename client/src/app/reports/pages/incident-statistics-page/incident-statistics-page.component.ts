import { MapsAPILoader } from '@agm/core';
import { ChangeDetectionStrategy, Component, OnDestroy, OnInit } from '@angular/core';
import { FormControl, FormGroup } from '@angular/forms';
import { select, Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { combineLatest, Observable, Subscription } from 'rxjs';
import { filter, map, skip, take, tap, withLatestFrom } from 'rxjs/operators';
import { environment } from '../../../../environments/environment';
import {
  INCIDENT_STATUSES,
  IncidentStatistics,
  IncidentStatisticsList,
  IncidentStatus,
  IncidentTagType,
  TagFilter,
  TagFilterMapping,
} from '../../reports';
import { GetIncidentStatisticsAction, ListIncidentStatisticsAction } from '../../reports.actions';
import {
  getIncidentStatistics,
  getIncidentStatisticsTotals,
  getStatisticsList,
  getStatisticsMonths,
  getTagList,
  getTagNameMapping,
  ReportsState,
  statisticsLoading,
} from '../../reports.state';


interface TagStats {
  [ key: string ]: {
    [P in IncidentStatus]: number;
  };
}

interface Chart {
  chartType: string;
  dataTable: (string | number)[][];
  columnNames: string[];
  options: google.visualization.BarChartOptions;
}

interface ItemMarker {
  lat: number;
  lon: number;
  markerIcon: google.maps.Icon;
  status: string;
  tags: string;
}

const DEFAULT_TAG_STATS = {
  [ IncidentStatus.NEW ]: 0,
  [ IncidentStatus.IN_PROGRESS ]: 0,
  [ IncidentStatus.RESOLVED ]: 0,
};

type StatusMapping = { [T in IncidentStatus]: { label: string; markerIcon: google.maps.Icon; } };

@Component({
  selector: 'oca-incident-statistics-page',
  templateUrl: './incident-statistics-page.component.html',
  styleUrls: ['./incident-statistics-page.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class IncidentStatisticsPageComponent implements OnInit, OnDestroy {
  statisticsLoading$: Observable<boolean>;
  statisticsList$: Observable<IncidentStatisticsList | null>;
  months$: Observable<{ [ key: number ]: number[] }>;
  filterableTagList$: Observable<TagFilter[]>;
  tagMapping$: Observable<TagFilterMapping>;
  categoryChart$: Observable<Chart | null>;
  totals$: Observable<{ value: IncidentStatus, label: string; amount: number; icon: string; color: string; }[]>;
  filteredChart: Chart | null = null;
  mapMarkers$: Observable<ItemMarker[]>;
  showMap$: Observable<boolean>;
  formGroup: FormGroup;
  yearControl = new FormControl();
  monthControl = new FormControl();
  tagControl = new FormControl([]);

  private subs: Subscription[] = [];
  private statusMapping$: Observable<StatusMapping>;

  constructor(private store: Store<ReportsState>,
              private translate: TranslateService,
              private mapsLoader: MapsAPILoader) {
    this.formGroup = new FormGroup({
      year: this.yearControl,
      month: this.monthControl,
      tag: this.tagControl,
    });
    // temp fix
    this.mapsLoader.load();
  }

  ngOnInit() {
    this.store.dispatch(new ListIncidentStatisticsAction());
    this.statisticsLoading$ = this.store.pipe(select(statisticsLoading));
    this.statisticsList$ = this.store.pipe(select(getStatisticsList), filter(list => list.categories.length > 0), tap(stats => {
      if (stats && stats.results.length) {
        const first = stats.results[ 0 ];
        this.yearControl.setValue(first.year);
        this.monthControl.setValue(first.months[ 0 ]);
      }
    }));
    this.months$ = this.store.pipe(select(getStatisticsMonths));
    this.subs.push(this.yearControl.valueChanges.pipe(withLatestFrom(this.months$)).subscribe(([year, stats]) => {
      this.monthControl.setValue(stats[ year ][ 0 ]);
    }));
    this.subs.push(this.monthControl.valueChanges.pipe(skip(1)).subscribe(month => {
      this.store.dispatch(new GetIncidentStatisticsAction({ year: this.yearControl.value, month }));
    }));
    const stats$ = this.store.pipe(select(getIncidentStatistics));
    const statsMapping$ = stats$.pipe(map(stats => this.getStatsMapping(stats)));
    this.filterableTagList$ = combineLatest([this.store.pipe(select(getTagList)), statsMapping$]).pipe(
      // Only return categories which have stats, so we don't show any buttons which don't do anything
      map(([tags, tagMapping]) => tags.filter(t => t.type === IncidentTagType.CATEGORY && t.id in tagMapping)),
    );
    this.tagMapping$ = this.store.pipe(select(getTagNameMapping));
    this.categoryChart$ = statsMapping$.pipe(
      withLatestFrom(this.tagMapping$),
      map(([tagMapping, tagNames]) => this.getTagChart(tagMapping, tagNames, (tag => tag.type === IncidentTagType.CATEGORY))),
    );
    const relatedTags$ = combineLatest([this.tagControl.valueChanges, stats$]).pipe(
      map(([tagFilter, stats]) => this.getRelatedTags(stats, tagFilter)),
    );
    this.subs.push(combineLatest([relatedTags$, statsMapping$, this.tagMapping$]).subscribe(([relatedTags, tagMapping, tagNames]) => {
      this.filteredChart = this.getTagChart(tagMapping, tagNames, (tag => relatedTags.includes(tag.id)));
    }));
    this.statusMapping$ = this.translate.get(INCIDENT_STATUSES.map(s => s.label)).pipe(map(translations => {
      const MARKER_SIZE = new google.maps.Size(24, 24);
      const { assetsBaseUrl } = environment;
      return ({
        [ IncidentStatus.NEW ]: {
          label: translations[ INCIDENT_STATUSES[ 0 ].label ],
          markerIcon: { url: `${assetsBaseUrl}/map-icon-red.svg`, scaledSize: MARKER_SIZE },
        },
        [ IncidentStatus.IN_PROGRESS ]: {
          label: translations[ INCIDENT_STATUSES[ 1 ].label ],
          markerIcon: { url: `${assetsBaseUrl}/map-icon-orange.svg`, scaledSize: MARKER_SIZE },
        },
        [ IncidentStatus.RESOLVED ]: {
          label: translations[ INCIDENT_STATUSES[ 2 ].label ],
          markerIcon: { url: `${assetsBaseUrl}/map-icon-green.svg`, scaledSize: MARKER_SIZE },
        },
      });
    }));
    this.mapMarkers$ = combineLatest([stats$, this.tagMapping$, this.statusMapping$]).pipe(
      map(([stats, tagMapping, statusMapping]) => {
        const markers: ItemMarker[] = [];
        for (const item of stats) {
          if (item.location) {
            const tags = item.tags.map(tag => tagMapping[ tag ].name).join(' - ');
            const lastStatus = item.statuses[ item.statuses.length - 1 ];
            const { markerIcon, label } = statusMapping[ lastStatus ];
            markers.push({ ...item.location, status: label, markerIcon, tags });
          }
        }
        return markers;
      }),
    );
    this.totals$ = this.store.pipe(select(getIncidentStatisticsTotals), map(totals => INCIDENT_STATUSES.map(status => ({
      ...status,
      amount: totals[ status.value ],
    }))));
    this.showMap$ = this.mapMarkers$.pipe(map(markers => markers.length > 0));
    this.subs.push(this.filterableTagList$.subscribe(tagList => {
      if (tagList.length > 0) {
        this.tagControl.setValue([tagList[ 0 ].id]);
      }
    }));
  }

  ngOnDestroy(): void {
    for (const sub of this.subs) {
      sub.unsubscribe();
    }
  }

  onMapReady($event: google.maps.Map) {
    this.statusMapping$.pipe(take(1)).subscribe(tagMapping => {
      const legend = document.createElement('div') as HTMLDivElement;
      legend.style.backgroundColor = 'rgba(255, 255, 255, .5)';
      legend.style.margin = '8px';
      legend.style.fontSize = '12px';
      legend.style.setProperty('backdrop-filter', 'blur(2px)');
      for (const { label, markerIcon } of Object.values(tagMapping)) {
        const div = document.createElement('div');
        div.style.display = 'flex';
        div.style.alignItems = 'center';
        div.style.padding = '4px';
        const img = document.createElement('img');
        img.src = markerIcon.url;
        img.alt = label;
        img.style.height = '24px';
        const span = document.createElement('span');
        span.textContent = ` ${label}`;
        div.appendChild(img);
        div.appendChild(span);
        legend.appendChild(div);
      }
      $event.controls[ google.maps.ControlPosition.LEFT_BOTTOM ].push(legend);
    });
  }

  toggleSelectedTag(tag: TagFilter) {
    let newTags: string[];
    if (this.tagControl.value.includes(tag.id)) {
      newTags = this.tagControl.value.filter((t: string) => t !== tag.id);
    } else {
      newTags = [...this.tagControl.value, tag.id];
    }
    this.tagControl.setValue(newTags);
  }

  private getStatsMapping(stats: IncidentStatistics[]): TagStats {
    const tagMapping: TagStats = {};
    for (const incidentStats of stats) {
      for (const tag of incidentStats.tags) {
        if (!(tag in tagMapping)) {
          tagMapping[ tag ] = { ...DEFAULT_TAG_STATS };
        }
        for (const status of incidentStats.statuses) {
          tagMapping[ tag ][ status ]++;
        }
      }
    }
    return tagMapping;
  }

  private getRelatedTags(stats: IncidentStatistics[], tags: string[]): string[] {
    const relatedTags = new Set<string>();
    for (const s of stats) {
      for (const checkTag of tags) {
        if (s.tags.some(t => tags.includes(t))) {
          for (const incidentTag of s.tags) {
            relatedTags.add(incidentTag);
          }
        }
      }
    }
    // Don't include the tags we're filtering on, we only want the other tags.
    for (const checkTag of tags) {
      relatedTags.delete(checkTag);
    }
    return [...relatedTags];
  }

  private getTagChart(tagMapping: TagStats, tagNames: TagFilterMapping, tagFilter: (item: TagFilter) => boolean): Chart | null {
    const tags = Object.values(tagNames).filter(tagFilter);
    const dataTable: [string, number, number, number][] = [];
    for (const tag of tags) {
      if (tag.id in tagMapping) {
        const stat = tagMapping[ tag.id ];
        dataTable.push([tag.name, stat[ IncidentStatus.NEW ], stat[ IncidentStatus.IN_PROGRESS ], stat[ IncidentStatus.RESOLVED ]]);
      }
    }
    if (!dataTable.length) {
      return null;
    }
    return {
      chartType: 'BarChart',
      dataTable,
      columnNames: [
        'Tag',
        this.translate.instant('oca.new'),
        this.translate.instant('oca.in_progress'),
        this.translate.instant('oca.resolved'),
      ],
      options: {
        width: 800,
        // Minimum 250 to ensure the horizontal axis shows up
        height: Math.max(250, dataTable.length * 100),
        backgroundColor: 'transparent',
        isStacked: false,
        legend: { position: 'right' },
        animation: { duration: 400, easing: 'inAndOut', startup: true },
        chartArea: { height: '85%', width: '60%' },
        colors: INCIDENT_STATUSES.map(s => s.color),
      },
    };
  }
}
