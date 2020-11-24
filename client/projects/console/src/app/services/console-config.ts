import { AppDetailPayload } from '../interfaces/apps.interfaces';
import { Injectable } from "@angular/core";


@Injectable()
export class ConsoleConfig  {
  public static RT_API_URL = '/console-api';
  public static BASE_PROXY_PATH = '/api/plugins/rcc/proxy';
  public static BUILDSERVER_URL = '/console-api/proxy';
  public static BUILDSERVER_API_URL = `${ConsoleConfig.BUILDSERVER_URL}/api`;

  public static appBaseUrl(appId: string) {
    return `${ConsoleConfig.BUILDSERVER_API_URL}/apps/${appId}`;
  }

  public static appBaseUrlRT(payload: AppDetailPayload | string) {
    return `${ConsoleConfig.RT_API_URL}/apps/${typeof payload === 'string' ? payload : payload.appId}`;
  }

}
