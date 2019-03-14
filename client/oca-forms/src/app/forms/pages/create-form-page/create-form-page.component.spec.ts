import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { CreateFormPageComponent } from './create-form-page.component';

describe('CreateFormPageComponent', () => {
  let component: CreateFormPageComponent;
  let fixture: ComponentFixture<CreateFormPageComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ CreateFormPageComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(CreateFormPageComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
