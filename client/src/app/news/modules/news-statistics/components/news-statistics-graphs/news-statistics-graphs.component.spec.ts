import { Component } from '@angular/core';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { NewsItemBasicStatistics, NewsItemTimeStatistics, NewsStats } from '@oca/web-shared';
import { TestingModule } from '../../../../../../testing/testing.module';
import { NewsStatisticsModule } from '../../news-statistics.module';
import { NewsStatisticsGraphsComponent, PossibleMetrics } from './news-statistics-graphs.component';

// @formatter:off
// tslint:disable-next-line
const data:NewsStats = {"news_item":{"app_ids":["rogerthat"],"buttons":[{"action":"http://192.168.193.217:8080/_ah/gcs/oca-files/services/service-847ced1d-8a60-44de-b225-3d06bded283f@rogerth.at/news/834.jpeg","caption":"Bijlage","flow_params":null,"id":"attachment"}],"flags":3,"group_type":"city","group_visible_until":null,"id":2543,"image_url":"dQw4w9WgXcQ","locations":null,"media":null,"message":"test bericht","published":true,"qr_code_caption":null,"qr_code_content":null,"role_ids":[],"scheduled_at":1592564447,"sender":{"avatar_id":5418393301680128,"email":"service-847ced1d-8a60-44de-b225-3d06bded283f@rogerth.at","name":"Gemeente Nazareth"},"sticky":false,"sticky_until":0,"tags":["news"],"target_audience":null,"timestamp":1592564447,"title":"Ingepland nieuwsbericht","type":1,"version":11},"statistics":{"action":{"age":[{"key":"0 - 5","value":27},{"key":"5 - 10","value":0},{"key":"10 - 15","value":0},{"key":"15 - 20","value":0},{"key":"20 - 25","value":1},{"key":"25 - 30","value":0},{"key":"30 - 35","value":8},{"key":"35 - 40","value":6},{"key":"40 - 45","value":8},{"key":"45 - 50","value":6},{"key":"50 - 55","value":10},{"key":"55 - 60","value":8},{"key":"60 - 65","value":12},{"key":"65 - 70","value":14},{"key":"70 - 75","value":8},{"key":"75 - 80","value":6},{"key":"80 - 85","value":0},{"key":"85 - 90","value":1},{"key":"90 - 95","value":0},{"key":"95 - 100","value":0},{"key":"100 - 105","value":0}],"gender":[{"key":"unknown","value":29},{"key":"male","value":49},{"key":"female","value":37}],"total":115},"id":2543,"reached":{"age":[{"key":"0 - 5","value":580},{"key":"5 - 10","value":0},{"key":"10 - 15","value":0},{"key":"15 - 20","value":1},{"key":"20 - 25","value":13},{"key":"25 - 30","value":33},{"key":"30 - 35","value":52},{"key":"35 - 40","value":91},{"key":"40 - 45","value":136},{"key":"45 - 50","value":183},{"key":"50 - 55","value":261},{"key":"55 - 60","value":311},{"key":"60 - 65","value":319},{"key":"65 - 70","value":286},{"key":"70 - 75","value":160},{"key":"75 - 80","value":52},{"key":"80 - 85","value":16},{"key":"85 - 90","value":7},{"key":"90 - 95","value":0},{"key":"95 - 100","value":0},{"key":"100 - 105","value":3}],"gender":[{"key":"unknown","value":591},{"key":"male","value":996},{"key":"female","value":917}],"total":2504}}};

// tslint:disable-next-line
const timeStats: NewsItemTimeStatistics = {"action":[{"time":"2020-06-23T09:00:00Z","value":18},{"time":"2020-06-23T10:00:00Z","value":22},{"time":"2020-06-23T11:00:00Z","value":13},{"time":"2020-06-23T12:00:00Z","value":8},{"time":"2020-06-23T13:00:00Z","value":4},{"time":"2020-06-23T14:00:00Z","value":6},{"time":"2020-06-23T15:00:00Z","value":6},{"time":"2020-06-23T16:00:00Z","value":5},{"time":"2020-06-23T17:00:00Z","value":4},{"time":"2020-06-23T18:00:00Z","value":4},{"time":"2020-06-23T19:00:00Z","value":8},{"time":"2020-06-23T20:00:00Z","value":3},{"time":"2020-06-23T21:00:00Z","value":2},{"time":"2020-06-23T22:00:00Z","value":0},{"time":"2020-06-23T23:00:00Z","value":0},{"time":"2020-06-24T00:00:00Z","value":1},{"time":"2020-06-24T01:00:00Z","value":0}],"id":2543,"reached":[{"time":"2020-06-23T09:00:00Z","value":135},{"time":"2020-06-23T10:00:00Z","value":226},{"time":"2020-06-23T11:00:00Z","value":176},{"time":"2020-06-23T12:00:00Z","value":166},{"time":"2020-06-23T13:00:00Z","value":164},{"time":"2020-06-23T14:00:00Z","value":164},{"time":"2020-06-23T15:00:00Z","value":204},{"time":"2020-06-23T16:00:00Z","value":166},{"time":"2020-06-23T17:00:00Z","value":183},{"time":"2020-06-23T18:00:00Z","value":183},{"time":"2020-06-23T19:00:00Z","value":133},{"time":"2020-06-23T20:00:00Z","value":86},{"time":"2020-06-23T21:00:00Z","value":55},{"time":"2020-06-23T22:00:00Z","value":23},{"time":"2020-06-23T23:00:00Z","value":12},{"time":"2020-06-24T00:00:00Z","value":3},{"time":"2020-06-24T01:00:00Z","value":1},{"time":"2020-06-24T02:00:00Z","value":6},{"time":"2020-06-24T03:00:00Z","value":9},{"time":"2020-06-24T04:00:00Z","value":21},{"time":"2020-06-24T05:00:00Z","value":64},{"time":"2020-06-24T06:00:00Z","value":84},{"time":"2020-06-24T07:00:00Z","value":87},{"time":"2020-06-24T08:00:00Z","value":64},{"time":"2020-06-24T09:00:00Z","value":89},{"time":"2020-06-24T10:00:00Z","value":0}]};
// @formatter:on
describe('NewsStatisticsGraphsComponent', () => {
  let component: TestComponent;
  let fixture: ComponentFixture<TestComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ TestComponent ],
      imports: [ TestingModule, NewsStatisticsModule ],
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(TestComponent);
    component = fixture.componentInstance;
  });

  it('should show a "no statistics available" warning', () => {
    component.timeStatistics = null;
    fixture.detectChanges();
    const p = fixture.debugElement.query(By.css('p'));
    expect(p).toBeTruthy('Expected a warning to be shown when no data is available');
  });

  it('should work with basic stats', () => {
    component.basicStatistics = data.statistics;
    fixture.detectChanges();
    const ageGraphs = fixture.debugElement.queryAll(By.css('google-chart'));
    expect(ageGraphs).toBeTruthy();
    expect(ageGraphs.length).toBe(3, 'Expected 3 charts');
    const p = fixture.debugElement.query(By.css('p'));
    expect(p).toBeNull('Expected warning to be hidden');
  });

  it('should hide old stats after choosing another metric which has no values', async () => {
    component.timeStatistics = timeStats;
    fixture.detectChanges();
    component.metric = 'action';
    fixture.detectChanges();
    await fixture.whenStable();
    const graphs = fixture.debugElement.queryAll(By.css('google-chart'));
    expect(graphs.length).toBe(0, 'Expected charts to be hidden');
  });
});

@Component({
  template: `
    <oca-news-statistics-graphs [basicStatistics]="basicStatistics"
                                [timeStatistics]="timeStatistics"
                                [selectedMetric]="metric"></oca-news-statistics-graphs>`,
})
export class TestComponent {
  basicStatistics: NewsItemBasicStatistics;
  timeStatistics: NewsItemTimeStatistics | null = null;
  metric: PossibleMetrics = 'reached';
}
