import { MapsAPILoader } from '@agm/core';
import { ChangeDetectionStrategy, Component, OnDestroy, OnInit } from '@angular/core';
import { FormControl, FormGroup } from '@angular/forms';
import { select, Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { combineLatest, Observable, Subscription } from 'rxjs';
import { filter, map, skip, tap, withLatestFrom } from 'rxjs/operators';
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
  dataTable: (string | number | Date)[][];
  columnNames: string[];
  options: any;
}

interface ItemMarker {
  lat: number;
  lon: number;
  status: string;
  tags: string;
}

const DEFAULT_TAG_STATS = {
  [ IncidentStatus.NEW ]: 0,
  [ IncidentStatus.IN_PROGRESS ]: 0,
  [ IncidentStatus.RESOLVED ]: 0,
};

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
  filteredChart$: Observable<Chart | null>;
  mapMarkers$: Observable<ItemMarker[]>;
  showMap$: Observable<boolean>;
  formGroup: FormGroup;
  yearControl = new FormControl();
  monthControl = new FormControl();
  tagControl = new FormControl();

  private subs: Subscription[] = [];

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
    this.filterableTagList$ = this.store.pipe(
      select(getTagList),
      map(tags => tags.filter(t => t.type === IncidentTagType.CATEGORY)),
      tap(tags => {
        if (tags.length) {
          this.tagControl.setValue([tags[ 0 ].id]);
        }
      }),
    );
    this.tagMapping$ = this.store.pipe(select(getTagNameMapping));
    const statsMapping$ = stats$.pipe(map(stats => this.getStatsMapping(stats)));
    this.categoryChart$ = statsMapping$.pipe(
      withLatestFrom(this.tagMapping$),
      map(([tagMapping, tagNames]) => this.getTagChart(tagMapping, tagNames, (tag => tag.type === IncidentTagType.CATEGORY))),
    );
    const relatedTags$ = combineLatest([this.tagControl.valueChanges, stats$]).pipe(
      map(([tagFilter, stats]) => this.getRelatedTags(stats, tagFilter)),
    );
    this.filteredChart$ = combineLatest([relatedTags$, statsMapping$, this.tagMapping$]).pipe(
      map(([relatedTags, tagMapping, tagNames]) =>
        this.getTagChart(tagMapping, tagNames, (tag => relatedTags.includes(tag.id)))),
    );
    const statusMapping$ = this.translate.get(INCIDENT_STATUSES.map(s => s.label)).pipe(map(translations => ({
      [ INCIDENT_STATUSES[ 0 ].value ]: translations[ INCIDENT_STATUSES[ 0 ].label ],
      [ INCIDENT_STATUSES[ 1 ].value ]: translations[ INCIDENT_STATUSES[ 1 ].label ],
      [ INCIDENT_STATUSES[ 2 ].value ]: translations[ INCIDENT_STATUSES[ 2 ].label ],
    })));
    this.mapMarkers$ = combineLatest([stats$, this.tagMapping$, statusMapping$]).pipe(
      map(([stats, tagMapping, statusMapping]) => {
        const markers: ItemMarker[] = [];
        for (const item of stats) {
          if (item.location) {
            const status = `${item.statuses.map(s => statusMapping[ s ]).join(', ')}`;
            const tags = item.tags.map(tag => tagMapping[ tag ].name).join(' - ');
            markers.push({ ...item.location, status, tags });
          }
        }
        return markers;
      }),
    );
    this.showMap$ = this.mapMarkers$.pipe(map(markers => markers.length > 0));
  }

  ngOnDestroy(): void {
    for (const sub of this.subs) {
      sub.unsubscribe();
    }
  }

  private getRelatedTags(stats: IncidentStatistics[], tags: string): string[] {
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
        height: 400,
        backgroundColor: 'transparent',
        isStacked: true,
        legend: { position: 'bottom' },
        animation: { duration: 1000, easing: 'out', startup: true },
        chartArea: { height: '85%' },
      },
    };
  }
}
