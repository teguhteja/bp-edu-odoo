import { session } from '@web/session';
import { patch } from '@web/core/utils/patch';

import { Dialog } from '@web/core/dialog/dialog';

patch(Dialog.prototype, {
  setup() {
    super.setup();
    this.data.size = (
        session.sbs_dialog_size !== 'maximize' ? this.props.size : 'fs'
    );
    this.data.sbsInitialSize = this.props?.size || 'lg';
  },
  onClickSbsDialogSizeToggle() {
      this.data.size = this.data.size === 'fs' ? this.data.sbsInitialSize : 'fs';
  }
});
