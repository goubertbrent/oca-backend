import { ChangeDetectionStrategy, Component, OnInit, ViewEncapsulation } from '@angular/core';
import { ActivatedRoute, ActivatedRouteSnapshot } from '@angular/router';
import { Store } from '@ngrx/store';
import { Observable } from 'rxjs';
import { ApiRequestStatus } from '../../../../../framework/client/rpc';
import { GetAppImagesAction, RemoveAppImageAction } from '../../../actions';
import { getAppImages, getAppImagesStatus } from '../../../console.state';
import { AppImageInfo } from '../../../interfaces';
import { ConsoleConfig } from '../../../services';

@Component({
  selector: 'rcc-appearance-images',
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.Emulated,
  templateUrl: 'images.component.html',
  styles: [`.image-card {
    display: inline-block;
    width: 200px;
    margin: 16px;
  }

  .image-container {
    height: 192px;
  }

  .image-card img {
    width: auto;
    max-height: 200px;
    max-width: 200px;
    margin-top: 0;
  }`],
})
export class AppearanceImagesComponent implements OnInit {
  imagesInfo$: Observable<AppImageInfo[]>;
  status$: Observable<ApiRequestStatus>;
  reloadImage = false;
  private appId: string;
  private timestamp = new Date().getTime();

  constructor(private store: Store,
              private route: ActivatedRoute) {
  }

  ngOnInit() {
    this.store.dispatch(new GetAppImagesAction());
    this.imagesInfo$ = this.store.select(getAppImages);
    this.status$ = this.store.select(getAppImagesStatus);
    this.appId = (<ActivatedRouteSnapshot>(<ActivatedRouteSnapshot>this.route.snapshot.parent).parent).params.appId;
    this.reloadImage = this.route.snapshot.queryParams.reloadImage;
  }

  removeImage(image: AppImageInfo) {
    this.store.dispatch(new RemoveAppImageAction(image));
  }

  getImageUrl(imageInfo: AppImageInfo) {
    const type = imageInfo.exists ? imageInfo.type : 'placeholder';
    let url = `${ConsoleConfig.BUILDSERVER_URL}/image/app/${this.appId}/${type}`;

    if (imageInfo.exists && this.reloadImage) {
      // because it's the same URL, add the time to force reload
      url += `?${this.timestamp}`;
    }

    return url;
  }
}
