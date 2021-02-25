import { ComponentFixture, TestBed } from '@angular/core/testing';

import { LayerbarComponent } from './layerbar.component';

describe('TopbarComponent', () => {
  let component: LayerbarComponent;
  let fixture: ComponentFixture<LayerbarComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ LayerbarComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(LayerbarComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
