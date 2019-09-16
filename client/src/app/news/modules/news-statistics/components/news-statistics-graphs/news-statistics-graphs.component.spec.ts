import { Component } from '@angular/core';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { TestingModule } from '../../../../../../testing/testing.module';
import { NewsApp, NewsItemStatistics } from '../../../../interfaces';
import { NewsStatisticsModule } from '../../news-statistics.module';
import { NewsStatisticsGraphsComponent, PossibleMetrics } from './news-statistics-graphs.component';

// @formatter:off
// tslint:disable-next-line
const data = {"apps":[{"type":1,"id":"be-berlare","name":"Berlare"},{"type":1,"id":"be-lokeren","name":"Lokeren"},{"type":1,"id":"be-wetteren","name":"Wetteren"},{"type":1,"id":"be-loc","name":"Lochristi"},{"type":1,"id":"be-zele","name":"Zele"},{"type":1,"id":"be-dendermonde","name":"Dendermonde"},{"type":1,"id":"be-wichelen","name":"Wichelen"},{"type":1,"id":"be-lede","name":"Lede"},{"type":1,"id":"be-laarne","name":"Laarne"},{"type":0,"id":"rogerthat","name":"Rogerthat"},{"type":1,"id":"be-destelbergen","name":"Destelbergen"}],"news_item":{"rogered":true,"role_ids":[],"feed_names":[{"app_id":"be-lede","name":"regional_news"},{"app_id":"be-lokeren","name":"regional_news"},{"app_id":"be-wetteren","name":"regional_news"},{"app_id":"be-loc","name":"regional_news"},{"app_id":"be-zele","name":"regional_news"},{"app_id":"be-dendermonde","name":"regional_news"},{"app_id":"be-wichelen","name":"regional_news"},{"app_id":"be-laarne","name":"regional_news"},{"app_id":"be-destelbergen","name":"regional_news"}],"action_count":1,"sticky":false,"app_ids":["be-berlare","be-lokeren","be-wetteren","be-loc","be-zele","be-dendermonde","be-wichelen","be-lede","be-laarne","rogerthat","be-destelbergen"],"message":"Planter's Punch\nJamaicaanse rum/fruitsap/kaneel/grenadine\nof alcoholvrije versie\n\nDuo mousse\nrode biet/look\n\nPintxo Serrano\ngerookte zalm/ei\n\nScampi\nguacamole\n\nGegrilde scheermesjes\npeterselie/olijfolie/look\n\nPresa Iberico\npaddenstoelen/paprikamarmelade\n\nGevulde aardappel\nspinazie/pijnboompitten/pompoencr\u00e8me\n\nZoete afsluiter\nframboos/yoghurt/milhojas/chocolade\n\nDonderdagavond 14 februari\nEnkel op reservatie\n\nPrijs menu \u20ac 50.00 per persoon\nAangepaste wijnen \u20ac 17.00\nBob formule \u20ac 10.00","id":401927004,"statistics":[{"action":{"gender":[{"value":0,"key":"unknown"},{"value":0,"key":"gender-male"},{"value":0,"key":"gender-female"}],"age":[{"value":0,"key":"0 - 5"},{"value":0,"key":"5 - 10"},{"value":0,"key":"10 - 15"},{"value":0,"key":"15 - 20"},{"value":0,"key":"20 - 25"},{"value":0,"key":"25 - 30"},{"value":0,"key":"30 - 35"},{"value":0,"key":"35 - 40"},{"value":0,"key":"40 - 45"},{"value":0,"key":"45 - 50"},{"value":0,"key":"50 - 55"},{"value":0,"key":"55 - 60"},{"value":0,"key":"60 - 65"},{"value":0,"key":"65 - 70"},{"value":0,"key":"70 - 75"},{"value":0,"key":"75 - 80"},{"value":0,"key":"80 - 85"},{"value":0,"key":"85 - 90"},{"value":0,"key":"90 - 95"},{"value":0,"key":"95 - 100"},{"value":0,"key":"100 - 105"}],"total":0,"time":[]},"reached":{"gender":[{"value":49,"key":"unknown"},{"value":265,"key":"gender-male"},{"value":281,"key":"gender-female"}],"age":[{"value":46,"key":"0 - 5"},{"value":0,"key":"5 - 10"},{"value":1,"key":"10 - 15"},{"value":1,"key":"15 - 20"},{"value":11,"key":"20 - 25"},{"value":21,"key":"25 - 30"},{"value":37,"key":"30 - 35"},{"value":66,"key":"35 - 40"},{"value":75,"key":"40 - 45"},{"value":81,"key":"45 - 50"},{"value":79,"key":"50 - 55"},{"value":57,"key":"55 - 60"},{"value":50,"key":"60 - 65"},{"value":39,"key":"65 - 70"},{"value":25,"key":"70 - 75"},{"value":3,"key":"75 - 80"},{"value":1,"key":"80 - 85"},{"value":1,"key":"85 - 90"},{"value":0,"key":"90 - 95"},{"value":0,"key":"95 - 100"},{"value":1,"key":"100 - 105"}],"total":595,"time":[{"timestamp":1549621166,"amount":18},{"timestamp":1549624766,"amount":12},{"timestamp":1549628366,"amount":8},{"timestamp":1549631966,"amount":5},{"timestamp":1549635566,"amount":5},{"timestamp":1549639166,"amount":3},{"timestamp":1549642766,"amount":6},{"timestamp":1549646366,"amount":3},{"timestamp":1549649966,"amount":5},{"timestamp":1549653566,"amount":2},{"timestamp":1549657166,"amount":6},{"timestamp":1549660766,"amount":6},{"timestamp":1549664366,"amount":2},{"timestamp":1549667966,"amount":2},{"timestamp":1549671566,"amount":1},{"timestamp":1549675166,"amount":2},{"timestamp":1549693166,"amount":2},{"timestamp":1549696766,"amount":97}]},"followed":{"gender":[{"value":0,"key":"unknown"},{"value":0,"key":"gender-male"},{"value":0,"key":"gender-female"}],"age":[{"value":0,"key":"0 - 5"},{"value":0,"key":"5 - 10"},{"value":0,"key":"10 - 15"},{"value":0,"key":"15 - 20"},{"value":0,"key":"20 - 25"},{"value":0,"key":"25 - 30"},{"value":0,"key":"30 - 35"},{"value":0,"key":"35 - 40"},{"value":0,"key":"40 - 45"},{"value":0,"key":"45 - 50"},{"value":0,"key":"50 - 55"},{"value":0,"key":"55 - 60"},{"value":0,"key":"60 - 65"},{"value":0,"key":"65 - 70"},{"value":0,"key":"70 - 75"},{"value":0,"key":"75 - 80"},{"value":0,"key":"80 - 85"},{"value":0,"key":"85 - 90"},{"value":0,"key":"90 - 95"},{"value":0,"key":"95 - 100"},{"value":0,"key":"100 - 105"}],"total":0,"time":[]},"app_id":"be-berlare","rogered":{"gender":[{"value":0,"key":"unknown"},{"value":1,"key":"gender-male"},{"value":2,"key":"gender-female"}],"age":[{"value":0,"key":"0 - 5"},{"value":0,"key":"5 - 10"},{"value":0,"key":"10 - 15"},{"value":0,"key":"15 - 20"},{"value":0,"key":"20 - 25"},{"value":0,"key":"25 - 30"},{"value":0,"key":"30 - 35"},{"value":0,"key":"35 - 40"},{"value":0,"key":"40 - 45"},{"value":1,"key":"45 - 50"},{"value":1,"key":"50 - 55"},{"value":0,"key":"55 - 60"},{"value":0,"key":"60 - 65"},{"value":0,"key":"65 - 70"},{"value":1,"key":"70 - 75"},{"value":0,"key":"75 - 80"},{"value":0,"key":"80 - 85"},{"value":0,"key":"85 - 90"},{"value":0,"key":"90 - 95"},{"value":0,"key":"95 - 100"},{"value":0,"key":"100 - 105"}],"total":3,"time":[{"timestamp":1549919966,"amount":1},{"timestamp":1549973966,"amount":1},{"timestamp":1556518766,"amount":1}]}},{"action":{"gender":[{"value":0,"key":"unknown"},{"value":0,"key":"gender-male"},{"value":0,"key":"gender-female"}],"age":[{"value":0,"key":"0 - 5"},{"value":0,"key":"5 - 10"},{"value":0,"key":"10 - 15"},{"value":0,"key":"15 - 20"},{"value":0,"key":"20 - 25"},{"value":0,"key":"25 - 30"},{"value":0,"key":"30 - 35"},{"value":0,"key":"35 - 40"},{"value":0,"key":"40 - 45"},{"value":0,"key":"45 - 50"},{"value":0,"key":"50 - 55"},{"value":0,"key":"55 - 60"},{"value":0,"key":"60 - 65"},{"value":0,"key":"65 - 70"},{"value":0,"key":"70 - 75"},{"value":0,"key":"75 - 80"},{"value":0,"key":"80 - 85"},{"value":0,"key":"85 - 90"},{"value":0,"key":"90 - 95"},{"value":0,"key":"95 - 100"},{"value":0,"key":"100 - 105"}],"total":0,"time":[]},"reached":{"gender":[{"value":4,"key":"unknown"},{"value":15,"key":"gender-male"},{"value":12,"key":"gender-female"}],"age":[{"value":3,"key":"0 - 5"},{"value":0,"key":"5 - 10"},{"value":0,"key":"10 - 15"},{"value":0,"key":"15 - 20"},{"value":2,"key":"20 - 25"},{"value":0,"key":"25 - 30"},{"value":1,"key":"30 - 35"},{"value":1,"key":"35 - 40"},{"value":7,"key":"40 - 45"},{"value":2,"key":"45 - 50"},{"value":6,"key":"50 - 55"},{"value":4,"key":"55 - 60"},{"value":2,"key":"60 - 65"},{"value":3,"key":"65 - 70"},{"value":0,"key":"70 - 75"},{"value":0,"key":"75 - 80"},{"value":0,"key":"80 - 85"},{"value":0,"key":"85 - 90"},{"value":0,"key":"90 - 95"},{"value":0,"key":"95 - 100"},{"value":0,"key":"100 - 105"}],"total":31,"time":[{"timestamp":1549635566,"amount":1},{"timestamp":1549653566,"amount":1},{"timestamp":1549696766,"amount":1},{"timestamp":1549700366,"amount":3},{"timestamp":1549703966,"amount":1},{"timestamp":1549725566,"amount":1},{"timestamp":1550297966,"amount":1},{"timestamp":1550351966,"amount":1},{"timestamp":1550866766,"amount":1},{"timestamp":1551291566,"amount":1},{"timestamp":1551349166,"amount":1},{"timestamp":1551374366,"amount":1},{"timestamp":1551410366,"amount":1},{"timestamp":1551449966,"amount":1},{"timestamp":1551536366,"amount":1},{"timestamp":1551730766,"amount":1},{"timestamp":1552335566,"amount":1},{"timestamp":1552457966,"amount":1},{"timestamp":1552990766,"amount":1},{"timestamp":1555827566,"amount":1},{"timestamp":1555935566,"amount":1},{"timestamp":1557177566,"amount":3},{"timestamp":1557249566,"amount":1},{"timestamp":1557299966,"amount":1},{"timestamp":1558459166,"amount":1},{"timestamp":1558804766,"amount":1},{"timestamp":1559290766,"amount":1}]},"followed":{"gender":[{"value":0,"key":"unknown"},{"value":0,"key":"gender-male"},{"value":0,"key":"gender-female"}],"age":[{"value":0,"key":"0 - 5"},{"value":0,"key":"5 - 10"},{"value":0,"key":"10 - 15"},{"value":0,"key":"15 - 20"},{"value":0,"key":"20 - 25"},{"value":0,"key":"25 - 30"},{"value":0,"key":"30 - 35"},{"value":0,"key":"35 - 40"},{"value":0,"key":"40 - 45"},{"value":0,"key":"45 - 50"},{"value":0,"key":"50 - 55"},{"value":0,"key":"55 - 60"},{"value":0,"key":"60 - 65"},{"value":0,"key":"65 - 70"},{"value":0,"key":"70 - 75"},{"value":0,"key":"75 - 80"},{"value":0,"key":"80 - 85"},{"value":0,"key":"85 - 90"},{"value":0,"key":"90 - 95"},{"value":0,"key":"95 - 100"},{"value":0,"key":"100 - 105"}],"total":0,"time":[]},"app_id":"be-lokeren","rogered":{"gender":[{"value":0,"key":"unknown"},{"value":0,"key":"gender-male"},{"value":0,"key":"gender-female"}],"age":[{"value":0,"key":"0 - 5"},{"value":0,"key":"5 - 10"},{"value":0,"key":"10 - 15"},{"value":0,"key":"15 - 20"},{"value":0,"key":"20 - 25"},{"value":0,"key":"25 - 30"},{"value":0,"key":"30 - 35"},{"value":0,"key":"35 - 40"},{"value":0,"key":"40 - 45"},{"value":0,"key":"45 - 50"},{"value":0,"key":"50 - 55"},{"value":0,"key":"55 - 60"},{"value":0,"key":"60 - 65"},{"value":0,"key":"65 - 70"},{"value":0,"key":"70 - 75"},{"value":0,"key":"75 - 80"},{"value":0,"key":"80 - 85"},{"value":0,"key":"85 - 90"},{"value":0,"key":"90 - 95"},{"value":0,"key":"95 - 100"},{"value":0,"key":"100 - 105"}],"total":0,"time":[]}},],"title":"Valentijnsmenu La Tapa Canaria","media":{"content":"https://rogerth.at/unauthenticated/news/image/423087004","width":533,"type":"image","height":200},"follow_count":0,"buttons":[{"action":"http://www.la-tapa-canaria.be/reservaties/","caption":"Reserveren","flow_params":"{}","id":"url"}],"version":1,"image_url":"https://rogerth.at/unauthenticated/news/image/423087004","type":1,"scheduled_at":0,"tags":["news"],"timestamp":1549621166,"reach":1246,"broadcast_type":"Nieuws","qr_code_caption":null,"sender":{"avatar_id":5782144819396608,"email":"latapacanaria@belgacom.net","name":"La Tapa Canaria"},"target_audience":null,"sticky_until":0,"flags":3,"users_that_rogered":["info@example.com:be-berlare","test@example.com:be-berlare","someone@example.com:be-berlare"],"published":true,"qr_code_content":null}};
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
    component.apps = [];
    component.newsStatistics = [];
    fixture.detectChanges();
    const p = fixture.debugElement.query(By.css('p'));
    expect(p).toBeTruthy('Expected a warning to be shown when no data is available');
  });

  it('should work with stats', () => {
    component.apps = data.apps;
    component.newsStatistics = data.news_item.statistics;
    fixture.detectChanges();
    const ageGraphs = fixture.debugElement.queryAll(By.css('google-chart'));
    expect(ageGraphs).toBeTruthy();
    expect(ageGraphs.length).toBe(3, 'Expected 3 charts');
    const p = fixture.debugElement.query(By.css('p'));
    expect(p).toBeNull('Expected warning to be hidden');
  });

  it('should hide old stats after choosing another metric which has no values', async () => {
    component.apps = data.apps;
    component.newsStatistics = data.news_item.statistics;
    fixture.detectChanges();
    component.metric = 'followed';
    fixture.detectChanges();
    await fixture.whenStable();
    const graphs = fixture.debugElement.queryAll(By.css('google-chart'));
    expect(graphs.length).toBe(0, 'Expected charts to be hidden');
  });
});

@Component({
  template: `
    <oca-news-statistics-graphs [apps]="apps"
                                [newsStatistics]="newsStatistics"
                                [selectedMetric]="metric"></oca-news-statistics-graphs>`,
})
export class TestComponent {
  apps: NewsApp[] | null = null;
  newsStatistics: NewsItemStatistics[] | null = null;
  metric: PossibleMetrics = 'reached';
}
