import { Observable } from 'rxjs';

export interface NavigationItem {
  description?: string;
  icon?: string;
  route: string;
  label: string;
}


export interface CheckListItem {
  label: Observable<string>;
  value: any;
  checked: boolean;
}
