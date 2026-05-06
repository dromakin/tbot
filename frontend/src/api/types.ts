export type MeOut = {
  tg_user_id: number;
  username: string | null;
  full_name: string;
  is_admin: boolean;
};

export type LectureOut = {
  id: number;
  number: number;
  title: string;
  description: string | null;
  topics: string | null;
  scheduled_at: string;
  format: 'online' | 'offline';
  stream_url: string | null;
  materials_url: string | null;
  registration_open: boolean;
  registration_opened_at: string | null;
};

export type StatsRowOut = {
  lecture_id: number;
  lecture_number: number;
  lecture_title: string;
  registrations_count: number;
  unique_clicks_count: number;
  total_clicks_count: number;
};

export type CourseOverviewOut = {
  lectures_total: number;
  lectures_open: number;
  lectures_past: number;
  registrations_total: number;
  unique_students: number;
  avg_registrations_per_lecture: number;
  attendance_rate: number;
  questions_pending_total: number;
  period_clicks_total: number;
};

export type LectureOverviewSparklinePointOut = {
  date: string;
  count: number;
};

export type LectureOverviewRowOut = {
  lecture_id: number;
  lecture_number: number;
  lecture_title: string;
  scheduled_at: string;
  registration_open: boolean;
  status: 'open' | 'closed_upcoming' | 'past';
  registrations: number;
  stream_link_unique: number;
  materials_lecture_unique: number;
  attendance_rate: number;
  sparkline: LectureOverviewSparklinePointOut[];
};

export type ClickEventType =
  | 'stream_link'
  | 'materials_general'
  | 'materials_lecture'
  | 'registration_click';

export type ClickTypeSettingOut = {
  event_type: ClickEventType;
  enabled: boolean;
};

export type ClickTypeStatsOut = {
  event_type: ClickEventType;
  total_clicks: number;
  unique_users: number;
};

export type LectureClickStatsOut = {
  lecture_id: number;
  lecture_number: number;
  lecture_title: string;
  stream_link_clicks: number;
  materials_lecture_clicks: number;
  registration_clicks: number;
  total_clicks: number;
};

export type ClickSummaryItemOut = {
  event_type: ClickEventType;
  today: number;
  week: number;
  all_time: number;
};

export type ClickSummaryTotalsOut = {
  today: number;
  week: number;
  all_time: number;
};

export type ClickSummaryOut = {
  items: ClickSummaryItemOut[];
  totals: ClickSummaryTotalsOut;
};

export type ClickTimeseriesPointOut = {
  date: string;
  event_type: ClickEventType;
  count: number;
};

export type ClickTopUserOut = {
  tg_user_id: number;
  username: string | null;
  username_at: string;
  full_name: string;
  clicks_count: number;
};

export type LectureFunnelOut = {
  lecture_id: number;
  registration_clicks: number;
  registrations: number;
  stream_link_unique: number;
  materials_lecture_unique: number;
};

export type LectureHourBucketOut = {
  bucket_start: string;
  event_type: ClickEventType;
  count: number;
};

export type RegistrationRowOut = {
  tg_user_id: number;
  username: string | null;
  username_at: string;
  full_name: string;
  registered_at: string;
  clicks_count: number;
};

export type QuestionStatus = 'pending' | 'ignored' | 'answered';

export type QuestionOut = {
  id: number;
  tg_user_id: number;
  username: string | null;
  username_at: string;
  full_name: string;
  text: string;
  status: QuestionStatus;
  answer_text: string | null;
  answered_at: string | null;
  answered_by_admin_id: number | null;
  answered_by_admin_username: string | null;
  created_at: string;
  updated_at: string;
};

export type LectureCreateIn = {
  number: number;
  title: string;
  description: string;
  topics: string | null;
  scheduled_at: string;
  format: 'online' | 'offline';
  stream_url: string | null;
  materials_url: string | null;
  registration_open: boolean;
};

export type LectureStreamIn = {
  stream_url: string | null;
};

export type LectureTopicsIn = {
  topics: string | null;
};

export type GeneralMaterialsSettingOut = {
  url: string | null;
};

export type GeneralMaterialsSettingIn = {
  url: string | null;
};

export type AutoCloseHoursOut = {
  hours: number;
};

export type AutoCloseHoursIn = {
  hours: number;
};

export type UserLectureOut = {
  lecture_id: number;
  lecture_number: number;
  lecture_title: string;
  description: string | null;
  scheduled_at: string;
  format: 'online' | 'offline';
  registration_open: boolean;
  is_registered: boolean;
  has_materials: boolean;
  has_stream: boolean;
};

export type UserMaterialsLectureOut = {
  lecture_id: number;
  lecture_number: number;
  lecture_title: string;
  scheduled_at: string;
  has_materials: boolean;
};

export type UserRegistrationOut = {
  lecture_id: number;
  lecture_number: number;
  lecture_title: string;
  scheduled_at: string;
  registered_at: string;
};

export type UserActionStatus =
  | 'ok'
  | 'already_registered'
  | 'closed'
  | 'not_found'
  | 'offline'
  | 'pending'
  | 'not_registered';

export type UserActionOut = {
  status: UserActionStatus;
  message: string;
  url: string | null;
};

export type UserStaticOut = {
  program_header: string;
  program_lectures: {
    number: number;
    title: string;
    topics: string[];
  }[];
  contact_text: string;
};
