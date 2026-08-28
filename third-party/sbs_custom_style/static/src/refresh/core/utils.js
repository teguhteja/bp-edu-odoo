import { session } from '@web/session';

const DEFAULT_INTERVAL = 30000;

export function getAutoLoadInterval() {
    return session.sbs_pager_autoload_interval ?? DEFAULT_INTERVAL;
}
