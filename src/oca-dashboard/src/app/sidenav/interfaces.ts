export interface SidebarItem {
  id: string;
  label: string;
  route: string;
  description?: string;
  icon?: string; // Should be one of https://material.io/icons/
  subItems?: SidebarItem[];
}
