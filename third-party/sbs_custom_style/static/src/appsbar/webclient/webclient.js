import { patch } from '@web/core/utils/patch';

import { WebClient } from '@web/webclient/webclient';
import { AppsBar } from '@sbs_custom_style/appsbar/webclient/appsbar/appsbar';

patch(WebClient, {
    components: {
        ...WebClient.components,
        AppsBar,
    },
});
