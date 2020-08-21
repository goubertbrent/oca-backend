export interface SidebarTitle {
  isTranslation: boolean;
  label: string;
  icon?: string;
  imageUrl?: string;
}

export interface SecondarySidebarItem {
  label: string;
  route: string;
  description?: string;
  icon?: string; // Should be one of https://material.io/icons/
}

export interface SidebarItem extends SecondarySidebarItem {
  id: string;
}
