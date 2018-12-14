import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { CreateNewsPageComponent } from './create-news-page.component';

describe('CreateNewsPageComponent', () => {
  let component: CreateNewsPageComponent;
  let fixture: ComponentFixture<CreateNewsPageComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ CreateNewsPageComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(CreateNewsPageComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
