import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import {
  App,
  AppAsset,
  AppColors,
  AppDetailPayload,
  AppImageInfo,
  AppMetaData,
  AppSearchParameters,
  AppSearchResult,
  AppSettings,
  AppSidebar,
  Branding,
  Build,
  BuildSettings,
  BulkUpdatePayload,
  CreateAppPayload,
  CreateBuildPayload,
  CreateDefaultBrandingPayload,
  DefaultBranding,
  EditAppAssetPayload,
  FileUploadPayload,
  GenerateImagesPayload,
  PatchAppCompletePayload,
  PatchAppPayload,
  QrCodeTemplate,
  RogerthatApp,
  SaveChangesPayload,
  UpdateAppImagePayload,
} from '../interfaces';
import { normalizeColorInput, normalizeColorOutput } from '../util';
import { ConsoleConfig } from './console-config';

@Injectable()
export class AppsService {

  constructor(private http: HttpClient) {
  }

  searchApps(params: AppSearchParameters) {
    let search: HttpParams = new HttpParams();
    if (params.query) {
      search = search.append('query', params.query);
    }
    search = search.append('fields', 'title,app_id');
    return this.http.get<AppSearchResult[]>(`${ConsoleConfig.BUILDSERVER_API_URL}/apps`, { params: search });
  }

  getApp(appId: string) {
    return this.http.get<App>(ConsoleConfig.appBaseUrl(appId))
      .pipe(map(app => this.convertApp(app)));
  }

  getApps() {
    return this.http.get<App[]>(`${ConsoleConfig.BUILDSERVER_API_URL}/apps`)
      .pipe(map(apps => apps.map(app => this.convertApp(app))));
  }

  getProductionApps() {
    return this.http.get<App[]>(`${ConsoleConfig.BUILDSERVER_API_URL}/apps/production`)
      .pipe(map(apps => apps.map(app => this.convertApp(app))));
  }

  createApp(app: CreateAppPayload) {
    return this.http.post<App>(`${ConsoleConfig.RT_API_URL}/apps`, app)
      .pipe(map(result => this.convertApp(result)));
  }

  updateApp(payload: App) {
    return this.http.put<App>(ConsoleConfig.appBaseUrl(payload.app_id), this.convertApp(payload, true))
      .pipe(map(app => this.convertApp(app)));
  }

  patchApp(appId: string, backendServer: string, payload: PatchAppPayload) {
    return this.http.put<PatchAppCompletePayload>(`${ConsoleConfig.RT_API_URL}/apps/${appId}/partial`, payload)
      .pipe(map(result => ({ ...result, app: this.convertApp(result.app) })));
  }

  getBuilds(appId: string) {
    return this.http.get<Build[]>(`${ConsoleConfig.appBaseUrl(appId)}/builds`);
  }

  createBuild(appId: string, payload: CreateBuildPayload) {
    return this.http.post<Build>(`${ConsoleConfig.appBaseUrl(appId)}/builds`, payload);
  }

  getRogerthatApp(appId: string) {
    return this.http.get<RogerthatApp>(`${ConsoleConfig.appBaseUrlRT(appId)}`);
  }

  getRogerthatApps() {
    return this.http.get<RogerthatApp[]>(`${ConsoleConfig.RT_API_URL}/apps`);
  }

  updateRogerthatApp(app: RogerthatApp) {
    return this.http.put<RogerthatApp>(`${ConsoleConfig.appBaseUrlRT(app.id)}`, app);
  }

  setDefaultApp(appId: string) {
    return this.http.post<RogerthatApp>(`${ConsoleConfig.appBaseUrlRT(appId)}/set-default`, {});
  }

  updateCoreBranding(appId: string, payload: FileUploadPayload) {
    return this.http.put<Branding>(`${ConsoleConfig.appBaseUrlRT(appId)}/core-branding`, { file: payload.file });
  }

  getQrCodeTemplates(appId: string) {
    return this.http.get<QrCodeTemplate[]>(`${ConsoleConfig.appBaseUrlRT(appId)}/qr-code-templates`);
  }

  addQrCodeTemplate(appId: string, payload: QrCodeTemplate) {
    return this.http.post<QrCodeTemplate>(`${ConsoleConfig.appBaseUrlRT(appId)}/qr-code-templates`, payload);
  }

  removeQrCodeTemplate(appId: string, payload: QrCodeTemplate) {
    const url = `${ConsoleConfig.appBaseUrlRT(appId)}/qr-code-templates/${payload.key_name}`;
    return this.http.delete<QrCodeTemplate>(url)
      .pipe(map(() => payload));
  }

  createDefaultQrCodeTemplate(appId: string, payload: string) {
    return this.http.post<QrCodeTemplate>(`${ConsoleConfig.appBaseUrlRT(appId)}/default-qr-code-template`, { file: payload });
  }

  getAppAssets(payload: AppDetailPayload) {
    return this.http.get<AppAsset[]>(`${ConsoleConfig.appBaseUrlRT(payload)}/assets`);
  }

  getBackendAppAssets() {
    return this.http.get<AppAsset[]>(`${ConsoleConfig.RT_API_URL}/assets`);
  }

  createAppAsset(asset: EditAppAssetPayload, appId: string) {
    const url = `/console-api/uploads/apps/${appId}/assets/${asset.kind}`;
    const data = new FormData();
    data.append('file', asset.file);
    data.append('scale_x', asset.scale_x.toString());
    return this.http.post<AppAsset>(url, data);
  }

  removeAppAsset(appId: string, payload: AppAsset) {
    return this.http.delete<AppAsset>(`${ConsoleConfig.appBaseUrlRT(appId)}/assets/${payload.kind}`)
      .pipe(map(() => payload));
  }

  getBackendAppAsset(assetId: string) {
    return this.http.get<AppAsset>(`${ConsoleConfig.RT_API_URL}/assets/${assetId}`);
  }

  updateBackendAppAsset(asset: EditAppAssetPayload) {
    const url = `/console-api/uploads/assets/${asset.id}`;
    return this.http.put<AppAsset>(url, this.getBackendAppAssetFormData(asset));
  }

  createBackendAppAsset(asset: EditAppAssetPayload) {
    const url = `/console-api/uploads/assets`;
    return this.http.post<AppAsset>(url, this.getBackendAppAssetFormData(asset));
  }

  removeBackendAppAsset(payload: AppAsset): Observable<AppAsset> {
    return this.http.delete<null>(`${ConsoleConfig.RT_API_URL}/assets/${payload.id}`)
      .pipe(map(() => payload));
  }

  getDefaultBrandings(appId: string) {
    return this.http.get<DefaultBranding[]>(`${ConsoleConfig.appBaseUrlRT(appId)}/default-brandings`);
  }

  createBackendBranding(appId: string, branding: CreateDefaultBrandingPayload) {
    const url = `/console-api/uploads/apps/${appId}/default-brandings/${branding.branding_type}`;
    const data = new FormData();
    data.append('file', branding.file);
    return this.http.post<DefaultBranding>(url, data);
  }

  removeDefaultBranding(appId: string, payload: DefaultBranding): Observable<DefaultBranding> {
    return this.http.delete<null>(`${ConsoleConfig.appBaseUrlRT(appId)}/default-brandings/${payload.branding_type}`)
      .pipe(map(() => payload));
  }

  getBackendBrandings() {
    return this.http.get<DefaultBranding[]>(`${ConsoleConfig.RT_API_URL}/default-brandings`);
  }

  getBackendBranding(brandingId: string) {
    return this.http.get<DefaultBranding>(`${ConsoleConfig.RT_API_URL}/default-brandings/${brandingId}`);
  }

  createGlobalBackendBranding(payload: CreateDefaultBrandingPayload): Observable<DefaultBranding> {
    const url = `/console-api/uploads/default-brandings`;
    return this.http.post<DefaultBranding>(url, this.getBackendBrandingFormData(payload));
  }

  updateBackendBranding(payload: CreateDefaultBrandingPayload): Observable<DefaultBranding> {
    const url = `/console-api/uploads/default-brandings/${payload.id}`;
    return this.http.put<DefaultBranding>(url, this.getBackendBrandingFormData(payload));
  }

  removeBackendBranding(branding: DefaultBranding): Observable<DefaultBranding> {
    return this.http.delete<null>(`${ConsoleConfig.RT_API_URL}/default-brandings/${branding.id}`)
      .pipe(map(() => branding));
  }

  getColors(appId: string): Observable<AppColors> {
    return this.http.get<AppColors>(`${ConsoleConfig.BUILDSERVER_API_URL}/apps/${appId}/colors`)
      .pipe(map(res => this.convertColors(res, true)));
  }

  updateColors(appId: string, payload: AppColors): Observable<AppColors> {
    const colors = this.convertColors({ ...payload }, false);
    return this.http.put<AppColors>(`${ConsoleConfig.BUILDSERVER_API_URL}/apps/${appId}/colors`, colors)
      .pipe(map(res => this.convertColors(res, true)));
  }

  getSidebar(appId: string): Observable<AppSidebar> {
    return this.http.get<AppSidebar>(`${ConsoleConfig.BUILDSERVER_API_URL}/apps/${appId}/sidebar`)
      .pipe(map(res => this.convertSidebar(res, true)));
  }

  updateSidebar(appId: string, payload: AppSidebar): Observable<AppSidebar> {
    const sidebar = this.convertSidebar({ ...payload }, false);
    return this.http.put<AppSidebar>(`${ConsoleConfig.BUILDSERVER_API_URL}/apps/${appId}/sidebar`, sidebar)
      .pipe(map(res => this.convertSidebar(res, true)));
  }

  getImages(appId: string): Observable<AppImageInfo[]> {
    return this.http.get<AppImageInfo[]>(`${ConsoleConfig.BUILDSERVER_API_URL}/apps/${appId}/images`);
  }

  getImage(appId: string, imageType: string): Observable<AppImageInfo> {
    return this.http.get<AppImageInfo>(`${ConsoleConfig.appBaseUrl(appId)}/images/${imageType}`);
  }

  updateImage(appId: string, payload: UpdateAppImagePayload): Observable<AppImageInfo[]> {
    const formData = new FormData();
    formData.append('file', payload.file);
    return this.http.put<AppImageInfo[]>(`${ConsoleConfig.appBaseUrl(appId)}/images/${payload.type}`, formData);
  }

  generateImages(appId: string, payload: GenerateImagesPayload): Observable<AppImageInfo[]> {
    const formData = new FormData();
    formData.append('file', payload.file);
    formData.append('types', payload.types.join(','));
    return this.http.put<AppImageInfo[]>(`${ConsoleConfig.appBaseUrl(appId)}/images/generate`, formData);
  }

  removeImage(appId: string, payload: AppImageInfo): Observable<AppImageInfo> {
    return this.http.delete<AppImageInfo>(`${ConsoleConfig.appBaseUrl(appId)}/images/${payload.type}`);
  }

  saveChanges(appId: string, payload: SaveChangesPayload): Observable<null> {
    return this.http.put(`${ConsoleConfig.appBaseUrl(appId)}/publish`, payload)
      .pipe(map(() => null));
  }

  revertChanges(appId: string): Observable<null> {
    return this.http.put(`${ConsoleConfig.appBaseUrl(appId)}/revert`, null)
      .pipe(map(() => null));
  }

  getBuildSettings(appId: string): Observable<BuildSettings> {
    return this.http.get<BuildSettings>(`${ConsoleConfig.appBaseUrl(appId)}/build-settings`);
  }

  updateBuildSettings(appId: string, buildSettings: BuildSettings): Observable<BuildSettings> {
    return this.http.put<BuildSettings>(`${ConsoleConfig.appBaseUrl(appId)}/build-settings`, buildSettings);
  }

  getAppSettings(appPayload: AppDetailPayload): Observable<AppSettings> {
    return this.http.get<AppSettings>(`${ConsoleConfig.appBaseUrlRT(appPayload)}/settings`);
  }

  updateAppSettings(appPayload: AppDetailPayload, appSettings: AppSettings): Observable<AppSettings> {
    return this.http.put<AppSettings>(`${ConsoleConfig.appBaseUrlRT(appPayload)}/settings`, appSettings);
  }

  saveAppSettingsFirebaseIos(appPayload: AppDetailPayload, file: string): Observable<AppSettings> {
    return this.http.put<AppSettings>(`${ConsoleConfig.appBaseUrlRT(appPayload)}/settings/firebase-ios`, { file });
  }

  updateFirebaseSettingsIos(appId: string, file: any): Observable<null> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.put(`${ConsoleConfig.appBaseUrl(appId)}/firebase-settings`, formData)
      .pipe(map(() => null));
  }

  updateFacebook(appId: string): Observable<null> {
    return this.http.post(`${ConsoleConfig.appBaseUrl(appId)}/facebook/update`, null)
      .pipe(map(() => null));
  }

  requestFacebookReview(appId: string): Observable<null> {
    return this.http.post(`${ConsoleConfig.appBaseUrl(appId)}/facebook/review`, null)
      .pipe(map(() => null));
  }

  getAppMetaData(appId: string): Observable<AppMetaData[]> {
    return this.http.get<AppMetaData[]>(`${ConsoleConfig.appBaseUrl(appId)}/metadata`);
  }

  updateAppMetaData(metadata: AppMetaData, appId: string): Observable<AppMetaData> {
    return this.http.post<AppMetaData>(`${ConsoleConfig.appBaseUrl(appId)}/metadata`, metadata);
  }

  getMetaDataDefaults(appType: number): Observable<AppMetaData[]> {
    return this.http.get<AppMetaData[]>(`${ConsoleConfig.BUILDSERVER_API_URL}/metadata/${appType}/defaults`);
  }

  bulkUpdateApps(options: BulkUpdatePayload): Observable<null> {
    return this.http.post(`${ConsoleConfig.BUILDSERVER_API_URL}/apps/bulk-update`, options)
      .pipe(map(() => null));
  }

  private convertColors(payload: AppColors, add: boolean) {
    if (add) {
      // RRGGBB -> #RRGGBB
      payload.app_tint_color = normalizeColorInput(payload.app_tint_color) as string;
      payload.primary_color = normalizeColorInput(payload.primary_color) as string;
      payload.homescreen_background = normalizeColorInput(payload.homescreen_background) as string;
      payload.homescreen_text = normalizeColorInput(payload.homescreen_text) as string;
      return payload;
    } else {
      // #RRGGBB|#RGB -> RRGGBB
      return {
        ...payload,
        app_tint_color: normalizeColorOutput(payload.app_tint_color) as string,
        primary_color: normalizeColorOutput(payload.primary_color) as string,
        homescreen_background: normalizeColorOutput(payload.homescreen_background) as string,
        homescreen_text: normalizeColorOutput(payload.homescreen_text) as string,
      };
    }
  }

  private convertSidebar(payload: AppSidebar, add: boolean) {
    if (add) {
      // RRGGBB -> #RRGGBB
      payload.color = (normalizeColorInput(payload.color) as string);
      payload.items.map(item => ({ ...item, color: normalizeColorInput(item.color) }));
      payload.toolbar.items.map(item => ({ ...item, color: normalizeColorInput(item.color) }));
      return payload;
    } else {
      // #RRGGBB|#RGB -> RRGGBB
      const sidebar: AppSidebar = JSON.parse(JSON.stringify(payload));
      sidebar.color = (normalizeColorOutput(sidebar.color) as string);
      sidebar.items.map(item => ({ ...item, color: normalizeColorOutput(item.color) }));
      sidebar.toolbar.items.map(item => ({ ...item, color: normalizeColorOutput(item.color) }));
      return sidebar;
    }
  }

  private getBackendAppAssetFormData(asset: EditAppAssetPayload) {
    const data = new FormData();
    if (asset.file) {
      data.append('file', asset.file);
    }
    data.append('asset_type', asset.kind);
    data.append('scale_x', asset.scale_x.toString());
    if (asset.app_ids) {
      data.append('app_ids', asset.app_ids.toString());
    }
    data.append('is_default', asset.is_default.toString());
    return data;
  }

  private getBackendBrandingFormData(payload: CreateDefaultBrandingPayload) {
    const data = new FormData();
    if (payload.file) {
      data.append('file', payload.file);
    }
    if (payload.app_ids) {
      data.append('app_ids', payload.app_ids.toString());
    }
    data.append('is_default', payload.is_default.toString());
    data.append('branding_type', payload.branding_type);
    return data;
  }

  private convertApp(app: App, reverse: boolean = false): App {
    if (reverse) {
      return {
        ...app,
        other_languages: (app.other_languages as string[]).join(','),
      };
    }
    return {
      ...app,
      other_languages: app.other_languages ? (app.other_languages as string).split(',') : [],
    };
  }
}
