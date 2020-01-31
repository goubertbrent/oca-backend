import { MapsAPILoader } from '@agm/core';
import { FormStyle, getLocaleMonthNames, TranslationWidth } from '@angular/common';
import { ChangeDetectionStrategy, Component, Inject, LOCALE_ID, OnDestroy, OnInit } from '@angular/core';
import { FormControl, FormGroup } from '@angular/forms';
import { select, Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { combineLatest, Observable, of, Subscription } from 'rxjs';
import { filter, map, take, tap, withLatestFrom } from 'rxjs/operators';
import { environment } from '../../../../environments/environment';
import { chunks, EMPTY_ARRAY } from '../../../shared/util';
import {
  Chart,
  INCIDENT_STATUSES,
  IncidentStatistics,
  IncidentStatisticsList,
  IncidentStatus,
  IncidentTagType,
  TagFilter,
  TagFilterMapping,
} from '../../reports';
import { GetIncidentStatisticsAction, ListIncidentStatisticsAction, SetIncidentStatsFilterAction } from '../../reports.actions';
import {
  getFilteredIncidentsStats,
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
    [P in IncidentStatus | 'total']: number;
  };
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
  total: 0,
};

type StatusMapping = { [T in IncidentStatus]: { label: string; markerIcon: any  /*google.maps.Icon*/; } };

@Component({
  selector: 'oca-incident-statistics-page',
  templateUrl: './incident-statistics-page.component.html',
  styleUrls: ['./incident-statistics-page.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class IncidentStatisticsPageComponent implements OnInit, OnDestroy {
  statisticsLoading$: Observable<boolean>;
  statisticsList$: Observable<IncidentStatisticsList | null>;
  yearValues$: Observable<number[]>;
  months$: Observable<{ [ key: number ]: number[] }>;
  filterableTagList$: Observable<TagFilter[]>;
  tagMapping$: Observable<TagFilterMapping>;
  categoryCharts$: Observable<Chart[]>;
  totals$: Observable<{ value: IncidentStatus, label: string; amount: number; icon: string; color: string; }[]>;
  filteredCharts$: Observable<Chart[]>;
  mapMarkers$: Observable<ItemMarker[]>;
  showMap$: Observable<boolean>;
  formGroup: FormGroup;
  yearControl = new FormControl([]);
  monthControl = new FormControl([]);
  tagControl = new FormControl([]);
  months: { value: number; label: string }[] = [];
  monthValues: number[] = [];

  private subs: Subscription[] = [];
  private statusMapping$: Observable<StatusMapping>;

  constructor(private store: Store<ReportsState>,
              private translate: TranslateService,
              private mapsLoader: MapsAPILoader,
              @Inject(LOCALE_ID) private currentLocale: string) {
    this.formGroup = new FormGroup({
      year: this.yearControl,
      month: this.monthControl,
      tag: this.tagControl,
    });
    // temp fix
    this.mapsLoader.load();
    this.months = getLocaleMonthNames(this.currentLocale, FormStyle.Standalone, TranslationWidth.Wide)
      .map((label, index) => ({ label, value: index + 1 }));
    this.monthValues = this.months.map(m => m.value);
  }

  ngOnInit() {
    this.store.dispatch(new ListIncidentStatisticsAction());
    this.statisticsLoading$ = this.store.pipe(select(statisticsLoading));
    this.statisticsList$ = this.store.pipe(select(getStatisticsList), filter(list => list.categories.length > 0), tap(stats => {
      if (stats && stats.results.length) {
        const first = stats.results[ 0 ];
        this.yearControl.setValue([first.year]);
        this.monthControl.setValue([new Date().getMonth() + 1]);
      }
    }));
    this.yearValues$ = this.statisticsList$.pipe(map(list => list ? list.results.map(r => r.year) : EMPTY_ARRAY));
    this.months$ = this.store.pipe(select(getStatisticsMonths));
    this.subs.push(combineLatest([this.yearControl.valueChanges, this.monthControl.valueChanges]).subscribe(([years, months]) => {
      this.fetchStats(years, months);
      this.store.dispatch(new SetIncidentStatsFilterAction({ years, months }));
    }));
    const stats$ = this.store.pipe(select(getFilteredIncidentsStats));
    const statsMapping$ = stats$.pipe(map(stats => this.getStatsMapping(stats)));
    this.filterableTagList$ = combineLatest([this.store.pipe(select(getTagList)), statsMapping$]).pipe(
      // Only return categories which have stats, so we don't show any buttons which don't do anything
      map(([tags, tagMapping]) => tags
        .filter(t => t.type === IncidentTagType.CATEGORY && t.id in tagMapping)
        .sort((first, second) => tagMapping[ second.id ].total - tagMapping[ first.id ].total)),
    );
    this.tagMapping$ = this.store.pipe(select(getTagNameMapping));
    this.categoryCharts$ = statsMapping$.pipe(
      withLatestFrom(this.tagMapping$),
      map(([tagMapping, tagNames]) => this.getPaginatedTagCharts(tagMapping, tagNames, (tag => tag.type === IncidentTagType.CATEGORY))),
    );
    const relatedTags$ = combineLatest([this.tagControl.valueChanges, stats$]).pipe(
      map(([tagFilter, stats]) => this.getRelatedTags(stats, tagFilter)),
    );
    this.filteredCharts$ = combineLatest([relatedTags$, statsMapping$, this.tagMapping$]).pipe(
      map(([relatedTags, tagMapping, tagNames]) =>
        this.getPaginatedTagCharts(tagMapping, tagNames, (tag => relatedTags.includes(tag.id))),
      ),
    );

    const MARKER_SIZE = { width: 24, height: 24 };
    const { assetsBaseUrl } = environment;
    const [newIncidents, inProgress, resolved] = INCIDENT_STATUSES;
    this.statusMapping$ = of({
      [ IncidentStatus.NEW ]: {
        label: this.translate.instant(newIncidents.label),
        markerIcon: { url: `${assetsBaseUrl}/${newIncidents.mapIcon}`, scaledSize: MARKER_SIZE },
      },
      [ IncidentStatus.IN_PROGRESS ]: {
        label: this.translate.instant(inProgress.label),
        markerIcon: { url: `${assetsBaseUrl}/${inProgress.mapIcon}`, scaledSize: MARKER_SIZE },
      },
      [ IncidentStatus.RESOLVED ]: {
        label: this.translate.instant(resolved.label),
        markerIcon: { url: `${assetsBaseUrl}/${resolved.mapIcon}`, scaledSize: MARKER_SIZE },
      },
    });
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
          tagMapping[ tag ].total++;
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

  private getPaginatedTagCharts(tagMapping: TagStats, tagNames: TagFilterMapping, tagFilter: (item: TagFilter) => boolean): Chart[] {
    const tags = Object.values(tagNames).filter(tagFilter);
    const dataTable: [string, number, number, number, number][] = [];
    for (const tag of tags) {
      if (tag.id in tagMapping) {
        const stat = tagMapping[ tag.id ];
        const n = stat[ IncidentStatus.NEW ];
        const p = stat[ IncidentStatus.IN_PROGRESS ];
        const r = stat[ IncidentStatus.RESOLVED ];
        dataTable.push([tag.name, n, p, r, n + p + r]);
      }
    }
    if (!dataTable.length) {
      return EMPTY_ARRAY;
    }
    // Sort by largest total amount of statuses
    const dataTables = dataTable.sort((first, second) => second[ 4 ] - first[ 4 ]).map((row) => {
      row.pop();
      return row;
    });
    const height = 500;
    const width = window.innerWidth - 16;
    const pageSize = 10;
    const results: Chart[] = [];
    for (const table of chunks(dataTables, pageSize)) {
      results.push({
        chartType: 'ColumnChart',
        dataTable: table,
        columnNames: [
          'Tag',
          ...INCIDENT_STATUSES.map(s => this.translate.instant(s.label)),
        ],
        options: {
          width,
          height,
          backgroundColor: 'transparent',
          legend: { position: 'top' },
          animation: { duration: 400, easing: 'inAndOut', startup: true },
          chartArea: { height: height - 100, width: width - 200 },
          colors: INCIDENT_STATUSES.map(s => s.color),
        },
      });
    }
    return results;
  }

  private fetchStats(years: number[], months: number[]) {
    const dates: string[] = [];
    for (const year of years) {
      for (const month of months) {
        dates.push(new Date(year, month - 1, 1).toISOString());
      }
    }
    this.store.dispatch(new GetIncidentStatisticsAction({ dates }));
  }
}
