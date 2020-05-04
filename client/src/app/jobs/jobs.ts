export const enum ContractType {
  // Same as the ones from vdab to make it ourselves easier
  FULLTIME = 'contract_type_001',
  TEMPORARY = 'contract_type_002',
  YOUTH_JOBS = 'contract_type_003',
  FREELANCE = 'contract_type_004',
  FLEXI_JOB = 'contract_type_005',
  SERVICE_CHECK_JOB = 'contract_type_006',
  VOLUNTEER_WORK = 'contract_type_007',
}

export const CONTRACT_TYPES = [
  { type: ContractType.FULLTIME, label: 'oca.fulltime' },
  { type: ContractType.TEMPORARY, label: 'oca.temporary' },
  { type: ContractType.YOUTH_JOBS, label: 'oca.youth_jobs' },
  { type: ContractType.FREELANCE, label: 'oca.freelance' },
  { type: ContractType.FLEXI_JOB, label: 'oca.flexijob' },
  { type: ContractType.SERVICE_CHECK_JOB, label: 'oca.service_check_job' },
  { type: ContractType.VOLUNTEER_WORK, label: 'oca.volunteer_work' },
];

export const enum JobDomain {
  PURCHASE = 'job_domain_001',
  ADMINISTRATION = 'job_domain_002',
  CONSTRUCTION = 'job_domain_003',
  COMMUNICATION = 'job_domain_004',
  CREATIVE = 'job_domain_005',
  FINANCIAL = 'job_domain_006',
  HEALTH = 'job_domain_007',
  HOSPITALITY_AND_TOURISM = 'job_domain_008',
  HUMAN_RESOURCES = 'job_domain_009',
  ICT = 'job_domain_010',
  LEGAL = 'job_domain_011',
  AGRICULTURE_AND_HORTICULTURE = 'job_domain_012',
  LOGISTICS_AND_TRANSPORT = 'job_domain_013',
  SERVICES = 'job_domain_014',
  MANAGEMENT = 'job_domain_015',
  MARKETING = 'job_domain_016',
  MAINTENANCE = 'job_domain_017',
  EDUCATION = 'job_domain_018',
  GOVERNMENT = 'job_domain_019',
  RESEARCH_AND_DEVELOPMENT = 'job_domain_020',
  PRODUCTION = 'job_domain_021',
  TECHNIC = 'job_domain_022',
  SALE = 'job_domain_023',
  OTHERS = 'job_domain_024',
}

export const JOB_DOMAINS = [
  { type: JobDomain.PURCHASE, label: 'oca.purchase' },
  { type: JobDomain.ADMINISTRATION, label: 'oca.administration' },
  { type: JobDomain.CONSTRUCTION, label: 'oca.construction' },
  { type: JobDomain.COMMUNICATION, label: 'oca.communication' },
  { type: JobDomain.CREATIVE, label: 'oca.creative' },
  { type: JobDomain.FINANCIAL, label: 'oca.financial' },
  { type: JobDomain.HEALTH, label: 'oca.health' },
  { type: JobDomain.HOSPITALITY_AND_TOURISM, label: 'oca.hospitality_and_tourism' },
  { type: JobDomain.HUMAN_RESOURCES, label: 'oca.human_resources' },
  { type: JobDomain.ICT, label: 'oca.ict' },
  { type: JobDomain.LEGAL, label: 'oca.legal' },
  { type: JobDomain.AGRICULTURE_AND_HORTICULTURE, label: 'oca.agriculture_and_horticulture' },
  { type: JobDomain.LOGISTICS_AND_TRANSPORT, label: 'oca.logistics_and_transport' },
  { type: JobDomain.SERVICES, label: 'oca.services' },
  { type: JobDomain.MANAGEMENT, label: 'oca.management' },
  { type: JobDomain.MARKETING, label: 'oca.marketing' },
  { type: JobDomain.MAINTENANCE, label: 'oca.maintenance' },
  { type: JobDomain.EDUCATION, label: 'oca.education' },
  { type: JobDomain.GOVERNMENT, label: 'oca.government' },
  { type: JobDomain.RESEARCH_AND_DEVELOPMENT, label: 'oca.research_and_development' },
  { type: JobDomain.PRODUCTION, label: 'oca.production' },
  { type: JobDomain.TECHNIC, label: 'oca.technic' },
  { type: JobDomain.SALE, label: 'oca.sale' },
  { type: JobDomain.OTHERS, label: 'oca.others' },
];

export const enum JobStatus {
  DELETED = -1,
  NEW,
  ONGOING,
  HIDDEN,
}

export const enum JobMatchSource {
  NO_MATCH,
  OCA,
  EXTERN
}

export const JOB_MATCH_SOURCES = [
  { type: JobMatchSource.NO_MATCH, label: 'oca.did_not_find_candidate' },
  { type: JobMatchSource.OCA, label: 'oca.our-city-app' },
  { type: JobMatchSource.EXTERN, label: 'oca.extern' },
];

export interface JobMatched {
  source: JobMatchSource;
  platform: string | null;
}

export interface JobOfferEmployer {
  name: string;
}

export interface JobOfferFunction {
  title: string;
  description: string;
}

export interface JobOfferLocation {
  city: string;
  geo_location: {
    lat: number;
    lon: number;
  } | null;
  street: string;
  street_number: string;
  country_code: string;
  postal_code: string;
}

export interface JobOfferContract {
  type: ContractType;
}

export interface JobOfferContactInformation {
  email: string;
  phone_number: string;
  website?: string | null;
}

export interface EditJobOffer {
  job_domains: JobDomain[];
  function: JobOfferFunction;
  employer: JobOfferEmployer;
  location: JobOfferLocation;
  contract: JobOfferContract;
  details: string;
  start_date: string | null;
  status: JobStatus;
  // Set as soon as the job is unpublished (from status ongoing -> hidden)
  match: JobMatched;
  contact_information: JobOfferContactInformation;
  profile: string;
}

export interface JobOffer extends EditJobOffer {
  id: number;
  internal_id: number;
}

export interface JobOfferList {
  results: JobOfferDetails[];
}

export interface JobOfferStatusChange {
  status: JobStatus;
  date: string;
}

export interface JobOfferStatistics {
  id: number;  // same id as JobOffer
  status_changes: JobOfferStatusChange[];
  // ids of those chats
  unread_solicitations: number[];
  // Null if not currently published
  publish_date: string | null;
}

export interface JobOfferDetails {
  offer: JobOffer;
  statistics: JobOfferStatistics;
}

// Job solicitation without user info
export interface PartialJobSolicitation {
  id: number;
  create_date: string;
  update_date: string;
  status: JobSolicitationStatus;
  last_message: JobSolicitationMessage;
}

export interface JobSolicitation extends PartialJobSolicitation {
  user_info: {
    name: string;
    email?: string;
    avatar_url?: string;
  };
}

export const enum JobSolicitationStatus {
  STATUS_UNREAD,
  STATUS_READ,
  DISABLED,
}

export interface NewSolicitationMessage {
  message: string;
}

export interface JobSolicitationMessage {
  id: number;
  reply: boolean;
  create_date: string;
  message: string;
}

export interface UIJobSolicitationMessage extends JobSolicitationMessage {
  createDate: Date;
  reply: boolean;
}

export interface JobSolicitationsList {
  results: JobSolicitation[];
}

export interface JobSolicitationMessageList {
  results: JobSolicitationMessage[];
}


export const enum JobNotificationType {
  NEW_SOLICITATION,
  HOURLY_SUMMARY,
}


export interface JobsSettings {
  notifications: JobNotificationType[];
  emails: string[];
}
